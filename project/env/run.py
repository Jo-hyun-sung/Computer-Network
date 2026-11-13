"""실험 1회 실행기 (P1).

하는 일:
  1. Mininet 실험망을 띄움 (topo.py)
  2. data/runs/<run_id>/meta.json 기록 (hosts.py에서 생성 → 토폴로지와 항상 일치)
  3. (선택) 스위치 전체 트래픽을 capture.pcap 으로 캡처
  4. 정상 트래픽을 흘림 (traffic/normal.py)
  5. 시나리오의 공격을 공격자 호스트에서 실행 (env/attacks/*)
  6. 공격 시작·끝 시각으로 labels.jsonl 기록 (data-format.md 2.1)
  7. 정리하고 종료

실행 (project/ 폴더에서, root 필요):
    sudo python3 env/run.py arp_spoof
    sudo python3 env/run.py mac_flood --no-pcap
    sudo python3 env/run.py arp_spoof --controller remote   # OS-Ken 붙일 때

완료 후 검사:
    python3 common/records.py check data/runs/<run_id>
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.records import make, write                      # noqa: E402
from env.hosts import HOSTS, SWITCH, by_name, by_role, one   # noqa: E402
from env.scenarios import Scenario, get                      # noqa: E402
from env.topo import LanTopo                                 # noqa: E402

HTTP_PORT = 8000


def _child_env() -> str:
    """호스트 안에서 공격·트래픽 스크립트를 실행할 때 붙이는 환경변수."""
    return f"PYTHONPATH={ROOT} LAB_OK=1 "


MON_PORT = "mon0"  # 캡처 전용 OVS 내부 포트 (호스트와 연결 안 됨)


def start_capture(net, pcap_path: Path):
    """스위치 s1의 모든 포트를 전용 모니터 포트(mon0)로 미러링해 pcap으로 저장.

    mon0은 호스트에 연결되지 않은 내부 포트라 트래픽을 주입하지 않고 복사본만 받습니다.
    실패하면 None을 돌려주고 캡처를 건너뜁니다. 오류는 capture.log에 남깁니다.
    """
    import subprocess
    log = pcap_path.with_suffix(".log")
    steps = [
        f"ovs-vsctl add-port {SWITCH} {MON_PORT} "
        f"-- set interface {MON_PORT} type=internal",
        f"ip link set {MON_PORT} up",
        f"ovs-vsctl -- --id=@p get port {MON_PORT} "
        f"-- --id=@m create mirror name=m0 select-all=true output-port=@p "
        f"-- set bridge {SWITCH} mirrors=@m",
    ]
    with open(log, "w") as lf:
        for cmd in steps:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            lf.write(f"$ {cmd}\n{r.stdout}{r.stderr}\n")
            if r.returncode != 0:
                print(f"[캡처] 설정 실패, 캡처 건너뜀 (자세한 내용 {log.name})")
                return None
    lf = open(log, "a")
    proc = subprocess.Popen(["tcpdump", "-i", MON_PORT, "-w", str(pcap_path), "-U"],
                            stdout=lf, stderr=lf)
    time.sleep(1.0)  # tcpdump가 뜰 시간
    if proc.poll() is not None:  # 이미 죽었으면
        print(f"[캡처] tcpdump 시작 실패 (자세한 내용 {log.name})")
        return None
    return proc


def stop_capture(proc) -> None:
    import subprocess
    if proc is not None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    subprocess.run(f"ovs-vsctl clear bridge {SWITCH} mirrors", shell=True,
                   capture_output=True)
    subprocess.run(f"ovs-vsctl --if-exists del-port {SWITCH} {MON_PORT}", shell=True,
                   capture_output=True)


def configure_network(net, procs: list) -> None:
    """게이트웨이 IP 포워딩, DNS 서버, 클라이언트 기본 경로 설정.

    dnsmasq는 popen으로 띄워 procs에 넣습니다. 그래야 종료 시 확실히 정리됩니다
    (`&`로 띄우면 net.stop() 뒤에도 살아남아 매 실험마다 쌓임).
    """
    gw = net.get(one("gateway").name)
    gw.cmd("sysctl -w net.ipv4.ip_forward=1")
    # *.lab.test 질의에 답하는 가벼운 DNS 서버
    procs.append(gw.popen(
        f"dnsmasq --no-daemon --listen-address={one('gateway').ip} "
        f"--no-resolv --bind-interfaces --address=/lab.test/{one('gateway').ip}",
        shell=True))
    for h in by_role("client") + by_role("attacker"):
        net.get(h.name).cmd(f"ip route add default via {one('gateway').ip} || true")


def write_meta(run_dir: Path, scn: Scenario, start_ts: float, end_ts: float) -> None:
    import json
    hosts = [{"name": h.name, "role": h.role, "mac": h.mac, "ip": h.ip,
              "sw": SWITCH, "port": h.port} for h in HOSTS]
    meta = {
        "v": 1,
        "run_id": run_dir.name,
        "scenario": scn.name,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "topology": f"single switch {SWITCH}, {len(HOSTS)} hosts",
        "hosts": hosts,
        "dhcp_servers": [h.mac for h in by_role("dhcp_server")],
        "notes": f"attack={scn.attack}, evasive={scn.evasive}",
    }
    (run_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_scenario(scn: Scenario, run_dir: Path, do_pcap: bool) -> None:
    from mininet.net import Mininet
    from mininet.node import OVSController, RemoteController
    from mininet.clean import cleanup

    cleanup()  # 이전 잔여물 정리
    ctrl = {"ovs": OVSController, "remote": RemoteController}[CONTROLLER]
    net = Mininet(topo=LanTopo(), controller=ctrl, autoSetMacs=False)
    net.start()

    procs = []
    cap = None
    run_start = time.time()
    try:
        configure_network(net, procs)
        if CONTROLLER == "ovs":
            net.waitConnected(timeout=10)

        if do_pcap:
            cap = start_capture(net, run_dir / "capture.pcap")

        # 정상 트래픽 시작: 게이트웨이 서버 + 클라이언트들
        gw = net.get(one("gateway").name)
        procs.append(gw.popen(
            f"{_child_env()}python3 -m env.traffic.normal --role server "
            f"--duration {scn.duration} --http-port {HTTP_PORT}", shell=True))
        for i, h in enumerate(by_role("client")):
            node = net.get(h.name)
            procs.append(node.popen(
                f"{_child_env()}python3 -m env.traffic.normal --role client "
                f"--duration {scn.duration} --http-port {HTTP_PORT} --seed {i}",
                shell=True))

        print(f"[run] 워밍업 {scn.warmup}초 (정상 트래픽만)")
        time.sleep(scn.warmup)

        # 공격 실행
        attacker = net.get(scn.attacker)
        iface = f"{scn.attacker}-eth0"
        cmd = (f"{_child_env()}python3 -m {scn.module} --iface {iface} "
               f"--duration {scn.attack_dur} " + " ".join(scn.args))
        print(f"[run] 공격 시작: {scn.attack} ({scn.attack_dur}초)")
        attack_start = time.time()
        aproc = attacker.popen(cmd, shell=True)
        aout, aerr = aproc.communicate()
        attack_end = time.time()
        if aproc.returncode != 0:
            print(f"[run] 공격 스크립트 종료코드 {aproc.returncode}")
            if aerr:
                print(aerr.decode(errors="replace")[:500])

        # label 기록
        atk = by_name(scn.attacker)
        tgt = by_name(scn.target) if scn.target else None
        with open(run_dir / "labels.jsonl", "w", encoding="utf-8") as fh:
            write(fh, make("label", ts=attack_end, attack_id="a01", attack=scn.attack,
                           start_ts=attack_start, end_ts=attack_end,
                           attacker=atk.endpoint(),
                           target=tgt.endpoint() if tgt else None,
                           evasive=scn.evasive, params=scn.params))

        print(f"[run] 쿨다운 {scn.cooldown}초")
        time.sleep(scn.cooldown)
        run_end = time.time()
        write_meta(run_dir, scn, run_start, run_end)
    finally:
        stop_capture(cap)
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        net.stop()


def main() -> None:
    global CONTROLLER
    if os.geteuid() != 0:
        sys.exit("root 권한이 필요합니다: sudo python3 env/run.py ...")
    p = argparse.ArgumentParser(description="실험 1회 실행기")
    p.add_argument("scenario", help="시나리오 이름 (arp_spoof, mac_flood, ...)")
    p.add_argument("--no-pcap", action="store_true", help="패킷 캡처 생략")
    p.add_argument("--controller", choices=["ovs", "remote"], default="ovs",
                   help="ovs=내장 컨트롤러(기본), remote=OS-Ken(6633 포트)")
    p.add_argument("--outdir", default=str(ROOT / "data" / "runs"))
    a = p.parse_args()
    CONTROLLER = a.controller

    scn = get(a.scenario)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + scn.name
    run_dir = Path(a.outdir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[run] 시나리오={scn.name} 폴더={run_dir}")
    run_scenario(scn, run_dir, do_pcap=not a.no_pcap)
    print(f"[run] 완료. 검사: python3 common/records.py check {run_dir}")


CONTROLLER = "ovs"

if __name__ == "__main__":
    main()
