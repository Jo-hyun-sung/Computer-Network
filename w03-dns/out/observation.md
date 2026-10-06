# Task 1 · Iterative resolver

A root server does not have the address of `www.korea.ac.kr` at all. It only knows who is responsible for the TLDs below it (`.kr`, `.com`, ...) and delegates the rest. If every domain were stored at the root there would be no point in having a hierarchy.

When I hit a delegation **without glue** (`www.stanford.edu`, 27 hops in total), I resolved that nameserver's own name again from the root. This seems to be where the "recursion" in "recursive resolver" comes from: every NS without glue adds one more whole root→TLD→authoritative round on top.

Most names needed only 3~6 servers to finish. My laptop's resolver covers this whole process by asking the resolver it is configured with **just once** — that is the convenience of a stub resolver.

# Task 2 · Does DNS really steer?

**Rule**: a site is third-party if the end of its CNAME chain is a different registered domain from the site's own and is not the same organization either.

**Where it was wrong**: `www.wikipedia.org` → `wikimedia.org`. A plain domain comparison calls it third-party, but it is really the same organization running its own infrastructure under a different domain name (the same pattern as `netflix.com` using its own CDN). The CNAME alone cannot tell "self-run" from "outsourced". In the other direction, `www.korea.ac.kr` has no CNAME at all, so this rule can never catch it even if it were hidden behind an anycast CDN.

**Steering number**:
- By resolver (one network): of 8 CDN-hosted sites, **7** gave a different address when I changed resolver.
- By network (home/lab Wi-Fi → phone tethering, B3): only **3 of 8** (Microsoft, Adobe, Apple — all Akamai) gave a different answer when the network changed. The other 5, on Fastly/Netlify, gave exactly the same answer. Akamai changes the DNS answer itself depending on where the client is, while Fastly/Netlify use anycast (the same IP announced from many places and routing sends you to the nearest one), so DNS does not need to change. So whether DNS steers depends on the CDN vendor.

**Part A (capture)**: a delegation and an answer are really the same DNS message format; only the filled-in sections differ. The root server's response (frame 2) has 0 answers and 6 NS records in authority — "I don't know, ask them". The authoritative server's response (frame 42) has 1 A record in the answer section and empty authority/additional — "I have it". The header flags cannot tell them apart; only the section contents can.

**Note**: when `test_tasks.py` is run inside the container, the capture check fails with "0 queries, 0 responses". That is not an empty capture: the harness compares `dns.flags.response` as the strings `"0"`/`"1"`, but tshark 4.2.2 in the container prints `True`/`False`, so it is a version issue. Running `tshark -r out/dns.pcapng -Y dns -T fields -e dns.flags.response` directly shows 22 queries and 22 responses.

# Task 3 · Cache improvement

Two problems in `BaselineCache`, with the same root cause (it never looks at the TTL):
- **Correctness bug**: it always caches for a fixed 60 seconds. For a record with TTL 20 s (`www.microsoft.com`) it keeps serving the answer for up to 60 s after expiry, which is where the 266 stale answers come from.
- **Performance bug**: `self.entries` is a list, so every lookup is a linear scan.

`YourCache` stores `(address, expiry time)` in a dict and goes upstream only when the entry has expired → 275 upstream queries, 0 stale.

**Floor**: 275 is the minimum for this workload. A cache that does not prefetch and only caches when a request arrives must go upstream once for each name's first request, and again every time a request arrives after that name's TTL has expired. `YourCache` re-fetches exactly at that boundary (`now >= expiry`), so there is no way to go lower (short of predicting the future). I also checked this by counting directly over the workload: fetching only when an entry has expired gives 275.

The record the baseline handles worst is `www.microsoft.com`: it has the shortest TTL (20 s) and is also the most frequently queried name, so the fixed 60 s policy produces the most stale answers there.
