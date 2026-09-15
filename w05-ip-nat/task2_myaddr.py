#!/usr/bin/env python3
"""Week 5 · Task 2 — Where exactly are you on the internet?

Textbook §4.3.2 (addressing, DHCP) and §4.3.3 (NAT).

This is the hands-on task. It asks what address your machine has, what address
the rest of the world sees, and why those two are usually different.

    python3 task2_myaddr.py --collect     # gather what your OS will tell you
    python3 task2_myaddr.py --report      # your analysis

Run it on **two networks**. Campus Wi-Fi and phone tethering behave differently
here, and the difference is the lesson.
"""
import argparse, json, os, platform, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def sh(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout
    except Exception as e:
        return f"<failed: {e}>"


def local_facts():
    """Raw output only. Reading it is your job, not this script's."""
    osname = platform.system()
    if osname == "Darwin":
        return {"os": osname,
                "ifconfig": sh("ifconfig"),
                "route": sh("route", "-n", "get", "default"),
                "dns": sh("scutil", "--dns")}
    if osname == "Linux":
        return {"os": osname,
                "ip_addr": sh("ip", "addr"),
                "ip_route": sh("ip", "route"),
                "dns": sh("cat", "/etc/resolv.conf")}
    return {"os": osname,
            "ipconfig": sh("ipconfig", "/all"),
            "route": sh("route", "print")}


def public_address():
    """What a server on the outside says your address is."""
    out = sh("curl", "-s", "--max-time", "10", "https://api.ipify.org")
    return out.strip() or None


def collect(label):
    os.makedirs(OUT, exist_ok=True)
    record = {"label": label, "local": local_facts(), "public": public_address()}
    path = os.path.join(OUT, "addresses.json")
    all_records = json.load(open(path)) if os.path.exists(path) else []
    all_records.append(record)
    json.dump(all_records, open(path, "w"), indent=2)
    print(f"  public address seen from outside: {record['public']}")
    print(f"  -> out/addresses.json  ({len(all_records)} record(s))")
    print("\n  Now read the raw output yourself and answer the questions in task2.md.")
    print("  The script deliberately does not parse it for you.")


def report():
    raise NotImplementedError(
        "write out/report.md by hand, or generate it - see task2.md")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--collect", metavar="LABEL",
                   help='where you are, e.g. "campus wifi"')
    p.add_argument("--report", action="store_true")
    a = p.parse_args()
    if a.collect:
        collect(a.collect)
    elif a.report:
        report()
    else:
        p.print_help()
