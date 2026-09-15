#!/usr/bin/env python3
"""Submission format check.

This does not grade your answers. It tells you what is missing.

    python3 check.py w03
"""
import sys, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))

# What has to be under each week's out/
# (filename, description, required)
SPEC = {
    "w02": ("w02-agent", [
        ("source-list.md",    "what the agent collected", True),
        ("analysis.md",       "its comparison table", True),
        ("verification.md",   "your hand check, ending with N of M", True),
        ("analysis-2.md",     "the table after your Task 3 setup", True),
        ("verification-2.md", "the second count", True),
        ("observation.md",    "2-3 lines per task", True),
    ]),
    "w03": ("w03-dns", [
        ("dns.pcapng",   "your own port 53 capture", False),
        ("chains.json",  "CNAME chains for every site", True),
        ("report.md",    "the steering study", True),
        ("bench.txt",    "python3 bench.py --yours", True),
        ("observation.md", "2-3 lines per task", True),
    ]),
    "w04": ("w04-tcp", [
        ("tcp.pcapng",     "your own handshake capture", False),
        ("throughput.json", "two or more labelled networks", True),
        ("bench.txt",      "python3 bench.py --yours", True),
        ("observation.md", "2-3 lines per task", True),
    ]),
    "w05": ("w05-ip-nat", [
        ("addresses.json", "two or more labelled networks", True),
        ("dhcp.pcapng",    "your own DORA capture", False),
        ("report.md",      "the address analysis", True),
        ("bench.txt",      "python3 bench.py --yours", True),
        ("observation.md", "2-3 lines per task", True),
    ]),
    "w06": ("w06-routing", [
        ("traceroute.txt",   "domestic, overseas, anycast", True),
        ("route-before.txt", "tables before the cut", True),
        ("route-after.txt",  "tables after the cut", True),
        ("reconverge.txt",   "measured reconvergence time", True),
        ("bench.txt",        "python3 bench.py --yours", True),
        ("observation.md",   "2-3 lines per task", True),
    ]),
    "w07": ("w07-ethernet-arp", [
        ("arp-before.txt", "ARP table before clearing", True),
        ("arp-after.txt",  "ARP table after refilling", True),
        ("arp.pcapng",     "request and reply on the wire", False),
        ("bench.txt",      "python3 bench.py --yours", True),
        ("observation.md", "2-3 lines per task", True),
    ]),
}


def check(week):
    if week not in SPEC:
        print(f"Unknown week: {week}")
        print("Try one of: " + " ".join(sorted(SPEC)))
        return 2

    folder, items = SPEC[week]
    out = os.path.join(HERE, folder, "out")
    print(f"== {folder}/out/ ==\n")

    if not os.path.isdir(out):
        print(f"  No out/ folder. Create it and put your results there:")
        print(f"      mkdir -p {folder}/out")
        return 1

    missing, weak = [], []
    for name, desc, required in items:
        path = os.path.join(out, name)
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size == 0:
                print(f"  [empty]  {name:20s} {desc}")
                missing.append(name)
            else:
                print(f"  [ok]     {name:20s} {desc}  ({size:,} bytes)")
        elif required:
            print(f"  [missing]{name:20s} {desc}")
            missing.append(name)
        else:
            # optional - may be absent if you took the official-trace route
            print(f"  [optional]{name:20s} {desc}  (not needed if you used the official trace)")

    # We only look at the length of the observation
    obs = os.path.join(out, "observation.md")
    if os.path.exists(obs):
        text = open(obs, encoding="utf-8").read().strip()
        lines = [l for l in text.splitlines() if l.strip()]
        if len(text) < 60:
            weak.append("observation.md is very short - 2-3 lines per task, please")
        elif len(lines) < 2:
            weak.append("observation.md is one line - 2-3 lines per task, please")

    print()
    for w in weak:
        print(f"  ! {w}")
    if missing:
        print(f"\n  {len(missing)} missing: {', '.join(missing)}")
        return 1
    if weak:
        print("\n  Format is fine. See the notes above.")
        return 0
    print("  Format check passed. Whether it is right is up to you.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    arg = sys.argv[1].lower()
    if not arg.startswith("w"):
        arg = "w" + arg.zfill(2)
    sys.exit(check(arg))
