# Task 2 · Where Exactly Are You on the Internet?

## Part A · KU wifi (network 1)

| | Value |
|---|---|
| Interface IPv4 address | `172.16.14.99` |
| Subnet mask | `255.255.255.0` (`/24`) |
| Default gateway | `172.16.14.1` |
| Public address (seen from outside) | `163.152.233.14` |

**A2 — subnet range, by hand:**
`172.16.14.99/24` → network `172.16.14.0`, host bits = 8.
- first usable: `172.16.14.1`
- last usable: `172.16.14.254`
- broadcast: `172.16.14.255`

Checked against `network_range("172.16.14.0/24")` from Task 1 → returns
`('172.16.14.1', '172.16.14.254', '172.16.14.255')`. Matches.

**A3 — default gateway:** `172.16.14.1` is inside `172.16.14.0/24`. It has to be:
a router can only be reached without another router's help (i.e. without an
extra routing hop) if it shares the same L2 segment/subnet as the host — the
host ARPs for the gateway's MAC address directly on the local link, which only
works if the gateway's address is within the host's own subnet.

**A4 — public address:** `163.152.233.14` (a Korea University-owned block).

**A5 — NAT layers:** `172.16.14.99` is RFC 1918 private (`172.16.0.0/12`), and
it differs from the public address `163.152.233.14`, so there is **at least
one NAT** between the laptop and the outside world. `163.152.233.14` is not in
`100.64.0.0/10` (the carrier-grade NAT range), so this looks like an ordinary
single-layer NAT at the campus border, not CGNAT. To tell one layer from two
for certain, `tracert`/`traceroute` to an outside host would show how many
private-address hops appear before the first public-address hop — one
private hop before reaching a public address would mean one NAT layer, two
would mean two.

## Part A/B · phone hotspot (network 2)

| | Value |
|---|---|
| Interface IPv4 address | `10.233.245.229` |
| Subnet mask | `255.255.255.0` (`/24`) |
| Default gateway | `10.233.245.221` |
| Public address (seen from outside) | `118.235.95.85` |

**Range check:** `10.233.245.0/24` → first usable `10.233.245.1`, last usable
`10.233.245.254`, broadcast `10.233.245.255`. Matches `network_range` from Task 1.

**Gateway:** `10.233.245.221` is inside `10.233.245.0/24` — same reasoning as A3.

**NAT layers:** `10.233.245.229` is RFC 1918 private (`10.0.0.0/8`), and the
public address `118.235.95.85` differs from it, so there is at least one NAT
here too — the phone itself, acting as the hotspot's router, NATs the laptop's
`10.233.245.x` address to whatever address the phone's own cellular data
connection holds. Whether the phone's own cellular address is itself public or
is a second, carrier-side NAT (common on mobile networks) cannot be told from
this data alone; it would take a traceroute from the laptop, or checking
whether the phone's own address (not visible to the laptop) falls in
`100.64.0.0/10`.

## Part B · Comparing the two networks

| | KU wifi | phone hotspot | changed? |
|---|---|---|---|
| Private address | `172.16.14.99` | `10.233.245.229` | yes |
| Mask | `/24` | `/24` | no |
| Gateway | `172.16.14.1` | `10.233.245.221` | yes |
| Public address | `163.152.233.14` | `118.235.95.85` | yes |

**B3:** Both the private and public addresses changed. This is expected —
they are two entirely different physical networks with different DHCP servers
(so a different private subnet is assigned) and different NAT devices at
their respective borders (so a different public address is presented to the
outside world). The same is true over time on one network: my earlier
measurement on KU wifi (a week ago) gave a different private and public
address than today's `172.16.14.99` / `163.152.233.14`, because the lease expires and the next one
may come from a different pool and NAT address. Nothing here is shared between
the two networks except the laptop's own hardware (MAC address), which is a
property of the NIC, not the network.

## Part C · DHCP capture

Captured with Wireshark/dumpcap (`port 67 or port 68`) on interface `Wi-Fi`
while running `ipconfig /release "Wi-Fi"` then `/renew` on KU wifi (frames
1-7), and then while joining the phone hotspot (frames 8-11). The KU wifi DORA
shares Transaction ID `0x0f1028be`:

| Frame | Message | Source | Destination | Lease time |
|---|---|---|---|---|
| 2 | Discover | `0.0.0.0` | `255.255.255.255` | — |
| 3 | Offer | `172.16.0.7` | `172.16.14.99` | 1800s |
| 4 | Request | `0.0.0.0` | `255.255.255.255` | — |
| 5 | ACK | `172.16.0.7` | `172.16.14.99` | 1800s |

Frame 1 is the `Release` that `ipconfig /release` sent (unicast from
`172.16.14.99` to the server `192.168.98.23`), not part of DORA. The hotspot
join (xid `0x14471249`, frames 8-11) is a second full DORA:
Discover `0.0.0.0`→`255.255.255.255`, Offer/ACK from `10.233.245.221` to
`10.233.245.229`, lease **3599s**.

**C1:** All four messages present for both networks — `out/dhcp.pcapng`.

**C2:** Discover's source is `0.0.0.0`, destination is `255.255.255.255`. The
strange one is the source: the client has no address yet (that's the whole
point of asking), so it has nothing valid to put in the source field and uses
`0.0.0.0`. That forces the destination to be the limited broadcast address —
there is no server address to unicast to either, since the client doesn't yet
know who or where the DHCP server is.

**C3:** Lease time offered/acknowledged on KU wifi: **1800 seconds (30
minutes)**. (Phone hotspot: 3599 s, about 1 hour; the ACK there also carries
renewal time T1 = 1799 s and rebinding time T2 = 3149 s.)

**C4:** Discover is broadcast at both L2 (`ff:ff:ff:ff:ff:ff`) and L3
(`255.255.255.255`) because neither the client's nor the server's address is
known yet. In the capture the Offer and ACK (frames 3 and 5) go to the
client's own MAC (L2 unicast), not `ff:ff:ff:ff:ff:ff`, and to the offered
`172.16.14.99` at L3 — and the DHCP broadcast flag is 0 in all of them. By
then the server has read the client's MAC out of the Discover packet itself
(the Ethernet source / DHCP `chaddr` field), so it can address the reply frame
directly to that MAC even though the client has no configured IP yet. The
Request (frame 4) is still broadcast because it also tells any *other* DHCP
server whose offer was not chosen that it can release it.

## Path (B) note

Live capture succeeded, so the official trace file was not needed.
