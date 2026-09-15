#!/usr/bin/env python3
"""Week 3 · Task 2 — Does DNS actually steer you? Measure it.

Textbook §2.4.3 (records) and §2.5 (CDNs).

The lecture claims two things:

    (a) most large sites are served by a CDN, reached through a CNAME chain
    (b) DNS steers each user to a *nearby* replica

Both are testable from your laptop, and one of them is harder to prove than
the slide makes it look. Your job is to produce the evidence and a number.

    python3 task2_steering.py --collect        # gather the raw data
    python3 task2_steering.py --report         # your analysis

What you have to build
----------------------
1.  For each hostname in SITES, follow the CNAME chain to its end and record
    every hop. `--collect` should leave the raw data in out/chains.json.

2.  Decide, for each site, whether it is served by a **third party**.
    This is the hard part and there is no single right answer:

      - `www.microsoft.com` ends at `akamaiedge.net`     - clearly third party
      - `www.netflix.com`   stops inside `netflix.com`   - own CDN, not third party
      - some sites have no CNAME at all and still sit behind a CDN (anycast)
      - `foo.cloudfront.net` and `foo.s3.amazonaws.com` are both Amazon,
        but they are not the same service

    Write down the rule you used and **defend it in observation.md**. A rule
    that just compares the last two labels will be wrong on at least one of
    the sites below; find which, and say so.

3.  Ask **two different resolvers** for the same name and compare the
    addresses you get back. If DNS really steers by location, a CDN-hosted
    name should answer differently to resolvers sitting in different places.

        RESOLVERS below has your system resolver and two public ones.

    Report: of N CDN-hosted sites, how many returned a different address set
    from a different resolver? Claim (b) predicts most of them. Check it.

Pass condition
--------------
There is no fixed answer. You pass by producing, in out/report.md:

  - the table: site | chain length | final zone | third party? | your rule's verdict
  - the steering number: "X of N sites answered differently to a different resolver"
  - at least one site where your classification rule was wrong, and why
"""
import argparse, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

SITES = [
    "www.microsoft.com",     # Akamai, multi-hop
    "www.netflix.com",       # own CDN
    "www.adobe.com",
    "www.cnn.com",
    "www.apple.com",
    "www.korea.ac.kr",       # no CDN at all
    "www.stanford.edu",
    "www.bbc.co.uk",
    "www.spotify.com",
    "www.github.com",
    "www.wikipedia.org",
    "www.nytimes.com",
]

RESOLVERS = {
    "system": None,          # whatever is in your resolv.conf
    "google": "8.8.8.8",
    "quad9":  "9.9.9.9",
}


def dig(name, rtype="A", server=None):
    """Raw lookup. Transport only - the thinking is yours."""
    args = ["dig", "+short", name, rtype]
    if server:
        args.insert(1, f"@{server}")
    out = subprocess.run(args, capture_output=True, text=True).stdout
    return [l.strip() for l in out.splitlines() if l.strip()]


# eTLD-ish suffixes that are two labels long but are NOT a registrable domain
# by themselves (a naive "last two labels" rule gets every one of these wrong).
TWO_LABEL_PUBLIC_SUFFIXES = {"co.kr", "ac.kr", "co.uk", "co.jp", "com.au"}

# domains that are unambiguously commercial CDN vendors - if the chain ends
# here, "third party" is not a judgment call.
KNOWN_CDN_VENDORS = {
    "akamai.net", "akamaiedge.net", "akamaitechnologies.com", "edgekey.net",
    "edgesuite.net", "fastly.net", "cloudflare.net", "cloudfront.net",
    "azureedge.net", "netlifyglobalcdn.com",
}


def registrable_domain(name):
    """Best-effort eTLD+1: last two labels, unless those two labels are
    themselves a known public suffix (co.kr, co.uk, ...), in which case take
    three."""
    labels = name.rstrip(".").lower().split(".")
    if len(labels) < 2:
        return name.lower()
    last_two = ".".join(labels[-2:])
    if last_two in TWO_LABEL_PUBLIC_SUFFIXES and len(labels) >= 3:
        return ".".join(labels[-3:])
    return last_two


def cname_chain(site, server=None, max_hops=10):
    """Follow CNAME -> CNAME -> ... until it stops or loops."""
    chain = [site]
    current = site
    seen = {site}
    for _ in range(max_hops):
        target = dig(current, "CNAME", server=server)
        if not target:
            break
        target = target[0].rstrip(".")
        chain.append(target)
        if target in seen:
            break
        seen.add(target)
        current = target
    return chain


def collect():
    """Gather raw chains and per-resolver answers into out/chains.json.

    For each site: follow the CNAME chain once (system resolver), then ask
    every resolver in RESOLVERS for the A records and keep each answer set.
    """
    data = {}
    for site in SITES:
        chain = cname_chain(site)
        addresses = {}
        for rname, rserver in RESOLVERS.items():
            addresses[rname] = sorted(dig(site, "A", server=rserver))
        data[site] = {"chain": chain, "final": chain[-1], "addresses": addresses}
        print(f"  {site:<20} {len(chain)} hop(s) -> {chain[-1]}")

    with open(os.path.join(OUT, "chains.json"), "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nwrote {len(data)} sites to out/chains.json")


def report():
    """Read out/chains.json and produce out/report.md.

    Classification rule: a site is on a third party if the registrable
    domain of the end of its CNAME chain differs from the site's own
    registrable domain. A site with no CNAME at all (chain length 1) is
    judged "not third party" by this rule BY CONSTRUCTION - it has nothing
    to compare - which is exactly where a domain-based rule is blind to
    anycast CDNs. That blind spot is reported explicitly below.
    """
    path = os.path.join(OUT, "chains.json")
    if not os.path.exists(path):
        raise SystemExit("run --collect first")
    with open(path) as f:
        data = json.load(f)

    rows = []
    naive_mismatches = []
    for site, info in data.items():
        chain, final = info["chain"], info["final"]
        own = registrable_domain(site)
        final_zone = registrable_domain(final)
        different_domain = final_zone != own
        # domain-only rule's verdict: any different registrable domain counts
        naive_third_party = different_domain
        # a same-organization-but-different-domain case (e.g. wikipedia.org
        # -> wikimedia.org) is NOT a commercial third party, and a pure
        # domain-comparison rule cannot tell the difference from Akamai/Fastly
        likely_own_org = (different_domain and final_zone not in KNOWN_CDN_VENDORS
                           and own.split(".")[0][:4] in final_zone.replace("-", ""))
        third_party = different_domain and not likely_own_org
        if likely_own_org:
            naive_mismatches.append((site, own, final_zone))

        rows.append({
            "site": site, "hops": len(chain), "final_zone": final_zone,
            "third_party": third_party, "naive_verdict": naive_third_party,
            "addresses": info["addresses"],
        })

    # steering: among sites we judged third-party (CDN-hosted), how many
    # got a different address SET from a different resolver?
    resolvers = list(next(iter(data.values()))["addresses"].keys())
    cdn_rows = [r for r in rows if r["third_party"]]
    steered = 0
    for r in cdn_rows:
        sets_ = [set(r["addresses"][res]) for res in resolvers]
        if len(set(map(frozenset, sets_))) > 1:
            steered += 1

    no_cname_but_should_check = [r["site"] for r in rows if r["hops"] == 1]

    lines = []
    lines.append("# Task 2 · DNS steering report\n")
    lines.append("Vantage point: single network (see observation.md for the second one).\n")
    lines.append("| site | chain length | final zone | third party? | rule's verdict |")
    lines.append("|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['site']} | {r['hops']} | {r['final_zone']} | "
                      f"{'yes' if r['third_party'] else 'no'} | "
                      f"{'yes' if r['naive_verdict'] else 'no'} |")

    lines.append("")
    lines.append(f"**Steering number**: {steered} of {len(cdn_rows)} CDN-hosted "
                  f"sites answered with a different address set to a different "
                  f"resolver (resolvers compared: {', '.join(resolvers)}).")

    lines.append("")
    lines.append("**Rule used**: a site is third-party if the CNAME chain ends in a "
                  "different registrable domain from the site's own AND that final "
                  "domain is not recognizably the same organization (own-org check: "
                  "not a known commercial CDN vendor, and shares a name fragment "
                  "with the site).")

    lines.append("")
    if naive_mismatches:
        s, o, f_ = naive_mismatches[0]
        lines.append(f"**Where a plain domain-comparison rule breaks**: `{s}` — the "
                      f"chain ends at `{f_}`, a different registrable domain from "
                      f"`{o}`, so a rule that only compares domains calls this "
                      f"'third party'. It is not: {f_.split('.')[0]} is the same "
                      f"organization running its own infrastructure under a second "
                      f"domain name, exactly like `netflix.com` does under its own "
                      f"name. You cannot tell these two cases apart from the DNS "
                      f"chain alone - it takes outside knowledge of who owns what.")
    blind = no_cname_but_should_check
    if blind:
        lines.append("")
        lines.append(f"**Also blind by construction**: {', '.join(blind)} has no "
                      "CNAME at all, so a domain-based rule always calls it "
                      "'not third party' - even if it were sitting behind an "
                      "anycast CDN with no CNAME to inspect, this rule would never "
                      "know.")

    with open(os.path.join(OUT, "report.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote out/report.md ({steered}/{len(cdn_rows)} steered)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--collect", action="store_true")
    p.add_argument("--report", action="store_true")
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.collect:
        collect()
    elif a.report:
        report()
    else:
        p.print_help()
