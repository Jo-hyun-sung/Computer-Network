# Task 1 · Iterative resolver

Root servers don't hand back an address for `www.korea.ac.kr` because they don't hold
that data at all — they only know which servers are authoritative for each TLD (`.kr`,
`.com`, ...). Storing every domain's records at the root would defeat the whole point of
the hierarchy (one write anywhere in the world would have to reach 13 machines).

When a delegation arrived without glue (this happened resolving `www.stanford.edu`,
27 hops total), I resolved the nameserver's own name with a fresh walk from the root
before I could even ask it anything — that's the extra recursion buried inside
"recursive resolver". Each no-glue NS costs one full extra root→TLD→auth walk.

Most names took 3–6 servers asked; the worst (Stanford, chained through several
no-glue nameservers) took ~27. My laptop's own resolver, by contrast, asks its
configured resolver exactly **one** question and lets it do all of this — the
convenience of a stub resolver is precisely that it outsources this walk.

# Task 2 · Does DNS steer you?

Rule used: a site is served by a third party if its CNAME chain ends in a different
registrable domain from the site's own, AND that final domain isn't recognizably the
same organization (not a known CDN vendor, doesn't share a name fragment with the site).

The rule got it wrong on `www.wikipedia.org`, which chains to `wikimedia.org` — a
different registrable domain, so a plain domain-comparison rule calls it "third party".
It isn't: Wikimedia is the same organization running its own infrastructure under a
second domain name, the same pattern as `netflix.com`'s own CDN. You cannot tell "own
infra under a second domain" apart from "outsourced to Akamai" using the DNS chain
alone; it takes outside knowledge of who owns what. Separately, `www.korea.ac.kr` has
no CNAME at all, so a domain-based rule is blind by construction to any anycast CDN
that might sit behind a bare A record.

Steering number: **7 of 8** CDN-hosted sites returned a different address set to a
different resolver (system / 8.8.8.8 / 9.9.9.9), measured from one network only —
this run was made from inside the lab container, so it is a single vantage point.
The second-network comparison (campus Wi-Fi vs. phone tethering) still needs to be
done to satisfy B3 — see the note in `out/report.md`.

Part A capture: a delegation and an answer are the exact same DNS message format —
the difference is only which sections are non-empty. The root server's response to
my A query for `www.korea.ac.kr` (frame 2) has 0 answers and instead fills the
authority section with 6 `NS` records (`b/c/d/e/f/g.dns.kr`) plus 10 glue records in
additional — it doesn't know the address, it only knows who to ask next. The
authoritative server's response (frame 42, same transaction pattern) has the
opposite shape: 1 `A` record in the answer section and nothing in authority or
additional — it actually holds the record. Nothing in the header flags marks one as
"delegation" and the other as "answer"; you can only tell by which section has
content.

# Task 3 · Beating the baseline cache

Two separate bugs in `BaselineCache`, both caused by the same root cause — it never
looks at the record's actual TTL:

- **Correctness bug**: it keeps every entry for a hardcoded `FIXED_LIFETIME = 60`
  seconds regardless of the record's real TTL. A record with a 3600s or 86400s TTL is
  evicted and re-fetched needlessly often *(performance)*, while a record with a 20s
  TTL (`www.microsoft.com`) is served for up to 60s after it actually expired
  *(correctness — this is where the 266 stale answers come from)*.
- **Performance bug**: `self.entries` is a list scanned linearly on every lookup.

`YourCache` stores `(address, expires_at)` in a dict keyed by name and only goes
upstream when `now >= expires_at`, using the record's real TTL. That produced 275
upstream queries with 0 stale answers.

**The floor**: 275 upstream queries *is* the floor for this workload. A cache that only
fetches on demand (no prefetching, which the harness doesn't allow anyway) must make
exactly one upstream call the first time each name is ever asked for, plus one more
call every time a later request for that name arrives after its previous record's TTL
has expired — there is no way to serve that request without either violating the TTL
(stale) or asking upstream again. `YourCache` already refreshes at exactly that
boundary (`now >= expires_at`, not before, not after), so it cannot go lower without
either predicting the future or breaking correctness.

The record the baseline mishandles worst is `www.microsoft.com`: it has both the
shortest real TTL (20s) and the highest Zipf query weight (most popular name in the
fixture), so the fixed-60s policy racks up the most stale hits on exactly the name that
is queried most often *and* changes fastest.
