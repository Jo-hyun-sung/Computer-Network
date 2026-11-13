"""pcap → 특징 기록(feat_host, feat_seg) 추출기 (P2, 오프라인).

실험 폴더 하나를 받아 capture.pcap을 읽고 features_1s.jsonl / features_5s.jsonl을 만듭니다.
형식은 docs/data-format.md 2.2, 2.3 을 따릅니다.

    python3 capture/extract.py data/runs/<run_id>

핵심 계산(data-format 2.2):
  - 캡처를 시각 순서로 훑으며 IP-MAC 대응표를 학습(처음 본 쌍 등록, DHCP ACK로 갱신).
  - ARP 응답/ Gratuitous ARP가 주장한 IP가 대응표에 다른 MAC으로 있으면 충돌(arp_ip_conflicts).
  - 최근 5초 내 해당 IP에 대한 who-has 요청이 없었던 ARP 응답은 미요청 응답(arp_rep_unsolicited).

오프라인 한계: 미러 pcap은 '들어온 스위치 포트'를 담지 않습니다. 그래서 포트는
meta.json의 MAC→포트로 역산하고, meta에 없는 MAC(플러딩용 가짜 MAC 등)은
포트 null 구간으로 묶습니다(data-format 2.3의 null 허용). 실시간 포트별 집계는 12주차.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.records import make, write  # noqa: E402

WINDOWS = (1, 5)
UNSOLICITED_WINDOW = 5.0  # 요청-응답을 짝지을 때 보는 시간(초)


def load_meta(run_dir: Path):
    import json
    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    mac2port = {}
    mac2ip = {}
    for h in meta["hosts"]:
        mac2port[h["mac"]] = (h["sw"], h["port"])
        mac2ip[h["mac"]] = h["ip"]
    return meta, mac2port, mac2ip


class HostAgg:
    """한 (창, MAC)의 집계."""
    __slots__ = ("pkts", "bytes", "arp_req", "arp_rep", "arp_grat",
                 "arp_rep_unsolicited", "claims", "conflicts",
                 "dhcp_offer", "dhcp_ack", "dhcp_discover",
                 "tcp_syn", "tcp_synack_in", "tcp_rst_in", "icmp_unreach_in",
                 "dns_resp", "dst_ip_count", "dst_port_set", "ip")

    def __init__(self):
        for f in self.__slots__:
            setattr(self, f, 0)
        self.claims = set()
        self.conflicts = set()
        self.dst_ip_count = defaultdict(int)
        self.dst_port_set = set()
        self.ip = None


class SegAgg:
    __slots__ = ("pkts", "bytes", "src_macs", "new_src_macs", "dhcp_discover",
                 "dhcp_chaddrs", "dhcp_offer", "dhcp_servers", "arp_rep", "tcp_syn")

    def __init__(self):
        for f in self.__slots__:
            setattr(self, f, 0)
        self.src_macs = set()
        self.new_src_macs = set()
        self.dhcp_chaddrs = set()
        self.dhcp_servers = set()


def extract(run_dir: Path) -> None:
    from scapy.all import (ARP, BOOTP, DHCP, DNS, ICMP, IP, TCP, UDP, Ether,
                           PcapReader)

    meta, mac2port, mac2ip = load_meta(run_dir)
    pcap = run_dir / "capture.pcap"
    if not pcap.exists():
        sys.exit(f"capture.pcap 없음: {run_dir} (run.py를 --no-pcap 없이 실행했는지 확인)")

    bindings: dict[str, str] = {}          # ip -> mac (학습된 대응표)
    recent_req: dict[str, float] = {}      # who-has 대상 ip -> 마지막 요청 시각
    seen_src_macs: set[str] = set()        # 지금까지 등장한 출발지 MAC(새 MAC 판정용)

    # 집계: win -> window_index -> key -> Agg
    host_agg: dict = {w: defaultdict(lambda: defaultdict(HostAgg)) for w in WINDOWS}
    seg_agg: dict = {w: defaultdict(lambda: defaultdict(SegAgg)) for w in WINDOWS}
    t0 = None

    def port_of(mac):
        return mac2port.get(mac, (None, None))

    for pkt in PcapReader(str(pcap)):
        if not pkt.haslayer(Ether):
            continue
        ts = float(pkt.time)
        if t0 is None:
            t0 = ts
        eth = pkt[Ether]
        smac, dmac = eth.src.lower(), eth.dst.lower()
        size = len(pkt)
        seen_new = smac not in seen_src_macs
        seen_src_macs.add(smac)
        sw, port = port_of(smac)

        # ARP 상태 갱신 (전역 시간순)
        is_unsolicited = conflict_ip = claim_ip = None
        arp_kind = None
        if pkt.haslayer(ARP):
            arp = pkt[ARP]
            psrc, pdst = arp.psrc, arp.pdst
            hwsrc = (arp.hwsrc or smac).lower()
            if arp.op == 1:          # who-has (요청)
                arp_kind = "req"
                recent_req[pdst] = ts
            elif arp.op == 2:        # is-at (응답)
                arp_kind = "rep"
                claim_ip = psrc
                # 미요청 응답?
                last = recent_req.get(psrc)
                is_unsolicited = (last is None) or (ts - last > UNSOLICITED_WINDOW)
                # 충돌? (대응표에 다른 MAC으로 등록된 IP를 주장)
                bound = bindings.get(psrc)
                if bound is not None and bound != hwsrc:
                    conflict_ip = psrc
                else:
                    bindings.setdefault(psrc, hwsrc)
            if arp.op == 2 and psrc == pdst:
                arp_kind = "grat"    # gratuitous

        # DHCP 메시지 종류
        dhcp_kind = None
        if pkt.haslayer(DHCP):
            for opt in pkt[DHCP].options:
                if isinstance(opt, tuple) and opt[0] == "message-type":
                    dhcp_kind = {1: "discover", 2: "offer", 3: "request",
                                 5: "ack"}.get(opt[1])
            # DHCP ACK는 대응표를 갱신(가장 신뢰)
            if dhcp_kind == "ack" and pkt.haslayer(BOOTP):
                yi = getattr(pkt[BOOTP], "yiaddr", None)
                if yi and yi != "0.0.0.0":
                    bindings[yi] = smac

        for w in WINDOWS:
            idx = int((ts - t0) // w)
            h = host_agg[w][idx][smac]
            h.pkts += 1
            h.bytes += size
            if pkt.haslayer(IP):
                ipl = pkt[IP]
                if h.ip is None:
                    h.ip = ipl.src
                h.dst_ip_count[ipl.dst] += 1
                if pkt.haslayer(TCP):
                    tcp = pkt[TCP]
                    if tcp.dport:
                        h.dst_port_set.add(int(tcp.dport))
                    flags = int(tcp.flags)
                    if flags & 0x02 and not flags & 0x10:
                        h.tcp_syn += 1
                elif pkt.haslayer(UDP):
                    if pkt[UDP].dport:
                        h.dst_port_set.add(int(pkt[UDP].dport))
                    if pkt.haslayer(DNS) and pkt[DNS].qr == 1:
                        h.dns_resp += 1
            if arp_kind == "req":
                h.arp_req += 1
            elif arp_kind in ("rep", "grat"):
                h.arp_rep += 1
                if arp_kind == "grat":
                    h.arp_grat += 1
                if is_unsolicited:
                    h.arp_rep_unsolicited += 1
                if claim_ip:
                    h.claims.add(claim_ip)
                if conflict_ip:
                    h.conflicts.add(conflict_ip)
            if dhcp_kind == "offer":
                h.dhcp_offer += 1
            elif dhcp_kind == "ack":
                h.dhcp_ack += 1
            elif dhcp_kind == "discover":
                h.dhcp_discover += 1

            # 받은 쪽(_in) 집계: 목적지 MAC 기준
            din = host_agg[w][idx].get(dmac)
            if din is not None or dmac in seen_src_macs:
                din = host_agg[w][idx][dmac]
                if pkt.haslayer(TCP):
                    f = int(pkt[TCP].flags)
                    if f & 0x12 == 0x12:
                        din.tcp_synack_in += 1
                    if f & 0x04:
                        din.tcp_rst_in += 1
                if pkt.haslayer(ICMP) and int(pkt[ICMP].type) == 3:
                    din.icmp_unreach_in += 1

            # 구간(포트) 집계 — meta로 포트 역산, 없으면 null 구간
            s = seg_agg[w][idx][(sw, port)]
            s.pkts += 1
            s.bytes += size
            s.src_macs.add(smac)
            if seen_new:
                s.new_src_macs.add(smac)
            if arp_kind in ("rep", "grat"):
                s.arp_rep += 1
            if pkt.haslayer(TCP) and int(pkt[TCP].flags) & 0x02 and not int(pkt[TCP].flags) & 0x10:
                s.tcp_syn += 1
            if dhcp_kind == "discover":
                s.dhcp_discover += 1
                ch = getattr(pkt[BOOTP], "chaddr", b"")[:6] if pkt.haslayer(BOOTP) else b""
                if ch:
                    s.dhcp_chaddrs.add(bytes(ch))
            elif dhcp_kind == "offer":
                s.dhcp_offer += 1
                s.dhcp_servers.add(smac)

    _emit(run_dir, host_agg, seg_agg, t0, mac2port, mac2ip)


def _emit(run_dir, host_agg, seg_agg, t0, mac2port, mac2ip):
    for w in WINDOWS:
        out = run_dir / f"features_{w}s.jsonl"
        with open(out, "w", encoding="utf-8") as fh:
            for idx in sorted(host_agg[w]):
                win_end = t0 + (idx + 1) * w
                for mac, h in sorted(host_agg[w][idx].items()):
                    if h.pkts == 0:
                        continue  # 보낸 게 없으면 기록 안 함
                    sw, port = mac2port.get(mac, (None, None))
                    total = sum(h.dst_ip_count.values())
                    top = max(h.dst_ip_count.values()) / total if total else 0.0
                    rec = make(
                        "feat_host", ts=win_end, win=w,
                        host={"mac": mac, "ip": h.ip or mac2ip.get(mac),
                              "sw": sw, "port": port},
                        pkts=h.pkts, bytes=h.bytes, arp_req=h.arp_req,
                        arp_rep=h.arp_rep, arp_grat=h.arp_grat,
                        arp_rep_unsolicited=h.arp_rep_unsolicited,
                        arp_ip_claims=len(h.claims), arp_ip_conflicts=len(h.conflicts),
                        dhcp_offer=h.dhcp_offer, dhcp_ack=h.dhcp_ack,
                        dhcp_discover=h.dhcp_discover, tcp_syn=h.tcp_syn,
                        tcp_synack_in=h.tcp_synack_in, tcp_rst_in=h.tcp_rst_in,
                        icmp_unreach_in=h.icmp_unreach_in,
                        dst_ips=len(h.dst_ip_count), dst_ports=len(h.dst_port_set),
                        top_dst_share=round(top, 4), dns_resp=h.dns_resp)
                    write(fh, rec)
            # feat_seg는 같은 파일에 이어서
            for idx in sorted(seg_agg[w]):
                win_end = t0 + (idx + 1) * w
                for (sw, port), s in sorted(
                        seg_agg[w][idx].items(),
                        key=lambda kv: (kv[0][0] or "", -1 if kv[0][1] is None else kv[0][1])):
                    rec = make(
                        "feat_seg", ts=win_end, win=w, sw=sw, port=port,
                        pkts=s.pkts, bytes=s.bytes, src_macs=len(s.src_macs),
                        new_src_macs=len(s.new_src_macs), dhcp_discover=s.dhcp_discover,
                        dhcp_chaddrs=len(s.dhcp_chaddrs), dhcp_offer=s.dhcp_offer,
                        dhcp_servers=len(s.dhcp_servers), arp_rep=s.arp_rep,
                        tcp_syn=s.tcp_syn)
                    write(fh, rec)
        print(f"[extract] {out.name} 작성")


def main() -> None:
    p = argparse.ArgumentParser(description="pcap → 특징 추출 (P2)")
    p.add_argument("run_dir")
    a = p.parse_args()
    extract(Path(a.run_dir))


if __name__ == "__main__":
    main()
