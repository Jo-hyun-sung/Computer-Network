#!/usr/bin/env python3
"""Week 3 · Task 1 — Build your own iterative resolver.

Textbook §2.4.2 - §2.4.3.

`dig +trace` walks root -> TLD -> authoritative for you. In this task you do
that walk yourself: start at a root server, read the delegation it returns,
ask the next server, and keep going until somebody answers authoritatively.

You may shell out to `dig` for the transport, or use a DNS library
(`dnspython` is in the container). Either is fine - what matters is that
*you* follow the delegations rather than letting a tool do it.

    python3 task1_resolve.py www.korea.ac.kr
    python3 task1_resolve.py --verify        # check yourself against dig

Pass condition
--------------
`--verify` resolves five names with your resolver and with `dig`, and the
addresses must agree. A name behind a CDN may legitimately return a different
address each time; the harness compares the *set of authoritative nameservers*
you ended at for those, not the address.
"""
import argparse, subprocess, sys

# Root servers. Everything starts here; there is no earlier step.
ROOT_SERVERS = [
    "198.41.0.4",       # a.root-servers.net
    "199.9.14.201",     # b.root-servers.net
    "192.33.4.12",      # c.root-servers.net
]

# (name, kind).  "stable" names must match dig exactly.  "cdn" names are served
# from many replicas and may legitimately give you a different address than dig
# got a second earlier - for those we only require that you reached an answer.
VERIFY_NAMES = [
    ("www.korea.ac.kr", "stable"),
    ("dns.google", "stable"),
    ("en.wikipedia.org", "stable"),
    ("www.stanford.edu", "stable"),
    ("www.microsoft.com", "cdn"),
]


class Resolver:
    """Your iterative resolver.

    The whole point is that you never ask a server to recurse for you.
    You ask one server, it says "not mine, ask over there", and you go there.

    Suggested shape - but it is yours to design:

        resolve(name) -> (address, path)
            address : the A record you ended up with, as a string
            path    : the servers you asked, in order, so you can show your work

    Things you will hit, in roughly this order:

    1.  A delegation gives you NS *names*, sometimes with glue A records and
        sometimes without. No glue means you have to resolve that nameserver's
        name first - which is another walk. Decide what you do there.
    2.  A server may not answer. Try the next one rather than giving up.
    3.  CNAMEs. The answer you get back may be a different name than the one
        you asked for, and you have to start again with that name.
    4.  Loops. Cap your depth.

    If you shell out to dig, the flag you want is `+norecurse`, so that the
    server you ask replies with a delegation instead of doing the work:

        dig @198.41.0.4 www.korea.ac.kr +norecurse
    """

    MAX_DEPTH = 20

    def resolve(self, name):
        self.path = []
        address = self._walk(name.rstrip(".").lower(), 0)
        return address, self.path

    def _walk(self, name, depth):
        """Iteratively resolve `name`, starting at the root every time we
        enter this level (fresh name -> fresh walk, per R5)."""
        servers = list(ROOT_SERVERS)
        while True:
            if depth > self.MAX_DEPTH:
                raise RuntimeError(f"depth exceeded resolving {name}")

            address, cname_target, delegation = self._ask(servers, name)

            if address is not None:
                return address

            if cname_target is not None:
                name = cname_target
                depth += 1
                servers = list(ROOT_SERVERS)
                continue

            if delegation is not None:
                ns_names, glue = delegation
                next_servers = []
                for ns in ns_names:
                    if ns in glue:
                        next_servers.extend(glue[ns])
                    else:
                        # no glue: resolve the nameserver's own name first
                        try:
                            next_servers.append(self._walk(ns, depth + 1))
                        except Exception:
                            continue
                if not next_servers:
                    raise RuntimeError(f"no usable nameserver for {name}")
                servers = next_servers
                depth += 1
                continue

            raise RuntimeError(f"no server answered for {name}")

    def _ask(self, servers, name):
        """Try each server in turn. Returns one of:
        (address, None, None)          - authoritative answer
        (None, cname_target, None)     - answer is a CNAME, follow it
        (None, None, (ns_names, glue)) - delegation
        (None, None, None)             - every server failed to answer
        """
        for server in servers:
            self.path.append(server)
            rrs = self._query(server, name)
            if not rrs:
                continue  # this server did not answer - try the next one

            for rr in rrs:
                if rr["type"] == "A" and rr["name"] == name:
                    return rr["data"], None, None

            for rr in rrs:
                if rr["type"] == "CNAME" and rr["name"] == name:
                    return None, rr["data"], None

            ns_names = [rr["data"] for rr in rrs if rr["type"] == "NS"]
            if ns_names:
                glue = {}
                for rr in rrs:
                    if rr["type"] == "A":
                        glue.setdefault(rr["name"], []).append(rr["data"])
                return None, None, (ns_names, glue)

        return None, None, None

    @staticmethod
    def _query(server, name):
        """One non-recursive query. Returns a flat list of {name, type, data}
        covering the answer, authority and additional sections - we don't
        need to tell them apart, only which name/type each record is for."""
        cmd = ["dig", f"@{server}", name, "A", "+norecurse",
               "+noall", "+answer", "+authority", "+additional",
               "+time=2", "+tries=1"]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=4).stdout
        except subprocess.TimeoutExpired:
            return None

        rrs = []
        for line in out.splitlines():
            if not line or line.startswith(";"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            rrname, _ttl, _cls, rrtype, rdata = parts[0], parts[1], parts[2], parts[3], parts[4]
            rrs.append({
                "name": rrname.rstrip(".").lower(),
                "type": rrtype,
                "data": rdata.rstrip(".").lower(),
            })
        return rrs


# ------------------------------------------------------------------- harness
def dig_answer(name):
    """What the system resolver says, for comparison."""
    out = subprocess.run(["dig", "+short", name, "A"],
                         capture_output=True, text=True).stdout
    return [l for l in out.split() if l and l[0].isdigit()]


def verify():
    r, failures = Resolver(), 0
    for name, kind in VERIFY_NAMES:
        try:
            addr, path = r.resolve(name)
        except NotImplementedError:
            print("Nothing implemented yet - write Resolver.resolve first.")
            return 1
        except Exception as e:
            print(f"  FAIL  {name:<22} your resolver raised {e!r}")
            failures += 1
            continue
        expected = dig_answer(name)
        if addr in expected:
            note = ""
        elif kind == "cdn":
            note = "  <- differs, but this name is CDN-hosted. Explain it."
        else:
            note = "  <- should have matched"
            failures += 1
        print(f"  {'FAIL' if note.endswith('matched') else 'ok  '}  {name:<22} "
              f"you={addr:<16} dig={','.join(expected) or '-'}   "
              f"hops={len(path)}{note}")
    print(f"\n  {len(VERIFY_NAMES) - failures}/{len(VERIFY_NAMES)} ok")
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("name", nargs="?", default="www.korea.ac.kr")
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()

    if a.verify:
        sys.exit(verify())

    addr, path = Resolver().resolve(a.name)
    for i, server in enumerate(path, 1):
        print(f"  {i}. asked {server}")
    print(f"\n  {a.name} -> {addr}")


if __name__ == "__main__":
    main()
