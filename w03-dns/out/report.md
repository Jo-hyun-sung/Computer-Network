# Task 2 · DNS steering report

## Part A · Capture (out/dns.pcapng)

Capture taken on my own machine (172.16.8.123) with filter `port 53`, running the
manual iterative walk for `www.korea.ac.kr` (root → `.kr` TLD → authoritative).
Trimmed to just this walk's traffic before submitting (root/TLD/authoritative IPs
only) to drop unrelated background-app lookups per the privacy note.

- **A2** — frame 41 (query, txn `0x0017`, A query for `www.korea.ac.kr` to
  `163.152.11.6`) / frame 42 (response, same txn `0x0017`, 1 answer:
  `www.korea.ac.kr` A `163.152.6.10`, TTL 3600).
- **A3** — **delegation**: frame 2, response from the root server (`198.41.0.4`)
  to the first A query — 0 answers, 6 `NS` records in authority
  (`b/c/d/e/f/g.dns.kr`) plus 10 glue records in additional, no answer section
  filled. **answer**: frame 42, response from the authoritative server
  (`163.152.11.6`) — 1 `A` record in the answer section, 0 authority, 0
  additional. Same DNS message format, different sections populated.
- **A4** — frame 30, **461 bytes** — the largest response captured. It is not
  one of the `www.korea.ac.kr` lookups; it's the response to an automatic PTR
  query nslookup made for the `.kr` TLD server's own IP
  (`1.61.101.210.in-addr.arpa`), answered by the root server with a delegation
  to the `in-addr-servers.arpa` zone: 6 `NS` records plus 6 `A` + 6 `AAAA` glue
  records (18 RRs total) is what inflates it past the plain `www.korea.ac.kr`
  delegations (383 bytes, 6 NS + 10 glue).

Vantage point: single network (see observation.md for the second one).

| site | chain length | final zone | third party? | rule's verdict |
|---|---|---|---|---|
| www.microsoft.com | 3 | akamaiedge.net | yes | yes |
| www.netflix.com | 2 | netflix.com | no | no |
| www.adobe.com | 3 | akamai.net | yes | yes |
| www.cnn.com | 2 | fastly.net | yes | yes |
| www.apple.com | 4 | akamaiedge.net | yes | yes |
| www.korea.ac.kr | 1 | korea.ac.kr | no | no |
| www.stanford.edu | 2 | netlifyglobalcdn.com | yes | yes |
| www.bbc.co.uk | 3 | fastly.net | yes | yes |
| www.spotify.com | 2 | fastly.net | yes | yes |
| www.github.com | 2 | github.com | no | no |
| www.wikipedia.org | 2 | wikimedia.org | no | yes |
| www.nytimes.com | 4 | fastly.net | yes | yes |

**Steering number**: 7 of 8 CDN-hosted sites answered with a different address set to a different resolver (resolvers compared: system, google, quad9).

**Rule used**: a site is third-party if the CNAME chain ends in a different registrable domain from the site's own AND that final domain is not recognizably the same organization (own-org check: not a known commercial CDN vendor, and shares a name fragment with the site).

**Where a plain domain-comparison rule breaks**: `www.wikipedia.org` — the chain ends at `wikimedia.org`, a different registrable domain from `wikipedia.org`, so a rule that only compares domains calls this 'third party'. It is not: wikimedia is the same organization running its own infrastructure under a second domain name, exactly like `netflix.com` does under its own name. You cannot tell these two cases apart from the DNS chain alone - it takes outside knowledge of who owns what.

**Also blind by construction**: www.korea.ac.kr has no CNAME at all, so a domain-based rule always calls it 'not third party' - even if it were sitting behind an anycast CDN with no CNAME to inspect, this rule would never know.
