# Week 5 · Observations

## Task 1 — Subnets and Longest-Prefix Match

`/32` returns first = last = broadcast = the address itself (no room for a
host range); `/31` returns first = network, last = broadcast (RFC 3021: both
addresses in a point-to-point pair are usable, there's no broadcast in the
ordinary sense). `10.20.30.70` matched all four `10.x` entries
(`10.0.0.0/8`, `10.20.0.0/16`, `10.20.30.0/24`, `10.20.30.64/26`); `/26`
(`lab-rack-2`) won because longest-prefix-match always prefers the more
specific route, regardless of insertion order. On a prefix-length tie I keep
whichever entry was added first — later duplicates at the same length are
silently ignored rather than overwriting.

## Task 2 — Where Exactly Are You

At least one NAT on both networks I measured: KU wifi's private address
(`172.16.5.58`, RFC 1918) differs from its public address (`163.152.233.5`,
a KU-owned block, not `100.64.0.0/10`), so one ordinary NAT at the campus
border. The phone hotspot showed the same pattern (`10.148.24.229` private
vs. `118.235.24.23` public) — plus a possible second NAT layer between the
phone and its carrier, which the laptop can't see directly. Between the two
networks, both the private address and the public address changed and
nothing stayed the same except the laptop's own MAC — different physical
networks mean different DHCP servers (different private subnet) and
different NAT borders (different public address). The DHCP Discover's source
address `0.0.0.0` couldn't be anything else: the client has no address to
put there yet, which is exactly why the destination has to be the broadcast
address instead of the (also unknown) server's address.

## Task 3 — Fast Longest-Prefix Match

Chose grouping by prefix length: a dict of `{prefix_len: {network: next_hop}}`,
checked longest-length-first, stopping at the first hit. Cost: one Python
dict per distinct prefix length actually used (at most 33), each holding all
entries of that length — roughly the same total memory as the linear list
plus dict overhead, no duplication of the routes themselves. R5: lookup time
is now proportional to the number of *distinct prefix lengths present*
(≤ 33), not to the number of routes (5,000) — each candidate length costs one
O(1) dict lookup instead of a full table scan. Measured: baseline 417
lookups/s vs. 1,309,552 lookups/s, a 3143.7x speedup, all 20,000 answers
identical to `LinearTable`. The bit-walk (binary trie) is what real hardware
builds because its cost is bounded by the address width (32 steps, fixed)
regardless of table size or language — a property a software hash table
doesn't need, since Python's dict already gives near O(1) lookups per prefix
length and 33 dict lookups beats walking a 32-level pointer-chasing trie in
an interpreted language.
