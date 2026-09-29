# Task 2 · Where Exactly Are You on the Internet?

## Part A · KU wifi (network 1)

| | Value |
|---|---|
| Interface IPv4 address | `172.16.5.58` |
| Subnet mask | `255.255.255.0` (`/24`) |
| Default gateway | `172.16.5.1` |
| Public address (seen from outside) | `163.152.233.5` |

**A2 — subnet range, by hand:**
`172.16.5.58/24` → network `172.16.5.0`, host bits = 8.
- first usable: `172.16.5.1`
- last usable: `172.16.5.254`
- broadcast: `172.16.5.255`

Checked against `network_range("172.16.5.0/24")` from Task 1 → returns
`('172.16.5.1', '172.16.5.254', '172.16.5.255')`. Matches.

**A3 — default gateway:** `172.16.5.1` is inside `172.16.5.0/24`. It has to be:
a router can only be reached without another router's help (i.e. without an
extra routing hop) if it shares the same L2 segment/subnet as the host — the
host ARPs for the gateway's MAC address directly on the local link, which only
works if the gateway's address is within the host's own subnet.

**A4 — public address:** `163.152.233.5` (a Korea University-owned block).

**A5 — NAT layers:** `172.16.5.58` is RFC 1918 private (`172.16.0.0/12`), and
it differs from the public address `163.152.233.5`, so there is **at least
one NAT** between the laptop and the outside world. `163.152.233.5` is not in
`100.64.0.0/10` (the carrier-grade NAT range), so this looks like an ordinary
single-layer NAT at the campus border, not CGNAT. To tell one layer from two
for certain, `tracert`/`traceroute` to an outside host would show how many
private-address hops appear before the first public-address hop — one
private hop before hitting `163.152.233.5`'s router would mean one NAT layer,
two would mean two.

## Part A/B · phone hotspot (network 2)

| | Value |
|---|---|
| Interface IPv4 address | `10.148.24.229` |
| Subnet mask | `255.255.255.0` (`/24`) |
| Default gateway | `10.148.24.39` |
| Public address (seen from outside) | `118.235.24.23` |
| IPv6 | present (`2001:e60:a56f:b55b::/64`) |

**Range check:** `10.148.24.0/24` → first usable `10.148.24.1`, last usable
`10.148.24.254`, broadcast `10.148.24.255`. Matches `network_range` from Task 1.

**Gateway:** `10.148.24.39` is inside `10.148.24.0/24` — same reasoning as A3.

**NAT layers:** `10.148.24.229` is RFC 1918 private (`10.0.0.0/8`), and the
public address `118.235.24.23` differs from it, so there is at least one NAT
here too — the phone itself, acting as the hotspot's router, NATs the laptop's
`10.148.24.x` address to whatever address the phone's own cellular data
connection holds. Whether the phone's own cellular address is itself public or
is a second, carrier-side NAT (common on mobile networks) cannot be told from
this data alone; it would take a traceroute from the laptop, or checking
whether the phone's own address (not visible to the laptop) falls in
`100.64.0.0/10`.

## Part B · Comparing the two networks

| | KU wifi | phone hotspot | changed? |
|---|---|---|---|
| Private address | `172.16.5.58` | `10.148.24.229` | yes |
| Mask | `/24` | `/24` | no |
| Gateway | `172.16.5.1` | `10.148.24.39` | yes |
| Public address | `163.152.233.5` | `118.235.24.23` | yes |

**B3:** Both the private and public addresses changed. This is expected —
they are two entirely different physical networks with different DHCP servers
(so a different private subnet is assigned) and different NAT devices at
their respective borders (so a different public address is presented to the
outside world). Nothing here is shared between the two networks except the
laptop's own hardware (MAC address), which is a property of the NIC, not the
network.

## Part C · DHCP capture

Captured by forcing a fresh lease on KU wifi (`ipconfig /release "Wi-Fi"` then
`/renew`) with Wireshark running (`port 67 or port 68`). All four DORA
messages share Transaction ID `0x659a3618`:

| # | Message | Source | Destination | Lease time |
|---|---|---|---|---|
| 1 | Discover | `0.0.0.0` | `255.255.255.255` | — |
| 2 | Offer | `172.16.0.7` | `172.16.5.58` | 1800s |
| 3 | Request | `0.0.0.0` | `255.255.255.255` | — |
| 4 | ACK | `172.16.0.7` | `172.16.5.58` | 1800s |

**C1:** All four messages present — `out/dhcp.pcapng`.

**C2:** Discover's source is `0.0.0.0`, destination is `255.255.255.255`. The
strange one is the source: the client has no address yet (that's the whole
point of asking), so it has nothing valid to put in the source field and uses
`0.0.0.0`. That forces the destination to be the limited broadcast address —
there is no server address to unicast to either, since the client doesn't yet
know who or where the DHCP server is.

**C3:** Lease time offered/acknowledged: **1800 seconds (30 minutes)**.

**C4:** Discover is broadcast at both L2 (`ff:ff:ff:ff:ff:ff`) and L3
(`255.255.255.255`) because neither the client's nor the server's address is
known yet. By the time of the Offer/ACK, the server has read the client's MAC
address out of the Discover packet itself (the Ethernet source / DHCP
`chaddr` field), so it can address the reply frame directly to that MAC as a
unicast, even before the client has a working IP configured. In this capture
the client also already had a specific address to request (`172.16.5.58`,
via the release/renew forcing a fresh DORA for the same lease), so the
IP-layer destination could be unicast too.

## Path (B) note

Live capture succeeded on the first working attempt (after forcing
release/renew to get a full DORA instead of just a lease renewal), so the
official trace file was not needed.
