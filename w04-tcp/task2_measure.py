#!/usr/bin/env python3
"""Week 4 · Task 2 — Measure your own link, more than once.

Textbook §3.5 (handshake, sequence numbers) and §3.7 (what limits throughput).

This is the hands-on task. The number it produces is about *your* connection at
*this* moment, and it will not be the same as anybody else's, or as your own an
hour from now. That is the finding, not a problem with the measurement.

    python3 task2_measure.py --label "campus wifi"
    python3 task2_measure.py --label "tethering"

Each run appends to out/throughput.json so you can compare them later.
"""
import argparse, json, os, statistics, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# A few hundred KB from a host that is not next door. Change it if it dies -
# and if you do, say so in observation.md, because the distance is part of
# what you are measuring.
TARGET = "https://speed.cloudflare.com/__down?bytes=5000000"
REPEATS = 5


def one_run():
    """One transfer. Returns (seconds, bytes, curl's own timing breakdown)."""
    fmt = "%{time_namelookup} %{time_connect} %{time_starttransfer} %{time_total} %{size_download}"
    r = subprocess.run(
        ["curl", "-s", "-o", os.devnull, "-w", fmt, TARGET],
        capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"curl failed: {r.stderr.strip() or r.returncode}")
    dns, conn, first, total, size = (float(x) for x in r.stdout.split())
    return {
        "dns_s": dns,
        "connect_s": conn - dns,        # this is your TCP handshake
        "ttfb_s": first - conn,
        "total_s": total,
        "bytes": int(size),
        "mbps": int(size) * 8 / total / 1e6 if total else 0,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--label", required=True,
                   help='where you are, e.g. "campus wifi" or "tethering"')
    p.add_argument("--repeats", type=int, default=REPEATS)
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)

    runs = []
    for i in range(a.repeats):
        r = one_run()
        runs.append(r)
        print(f"  {i + 1}/{a.repeats}  {r['mbps']:7.2f} Mbps   "
              f"handshake {r['connect_s'] * 1000:6.1f} ms   "
              f"ttfb {r['ttfb_s'] * 1000:6.1f} ms")
        time.sleep(1)

    mbps = [r["mbps"] for r in runs]
    record = {
        "label": a.label,
        "when": time.strftime("%Y-%m-%d %H:%M:%S"),
        "target": TARGET,
        "runs": runs,
        "mbps_median": statistics.median(mbps),
        "mbps_min": min(mbps),
        "mbps_max": max(mbps),
        "handshake_ms_median": statistics.median(
            r["connect_s"] * 1000 for r in runs),
    }

    path = os.path.join(OUT, "throughput.json")
    all_records = json.load(open(path)) if os.path.exists(path) else []
    all_records.append(record)
    json.dump(all_records, open(path, "w"), indent=2)

    spread = (max(mbps) - min(mbps)) / statistics.median(mbps) if mbps else 0
    print(f"\n  {a.label}:  median {record['mbps_median']:.2f} Mbps, "
          f"spread {spread:.0%} across {a.repeats} runs")
    print(f"  handshake median {record['handshake_ms_median']:.1f} ms")
    print(f"  -> out/throughput.json  ({len(all_records)} record(s) so far)")


if __name__ == "__main__":
    main()
