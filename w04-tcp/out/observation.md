# w04-tcp observations

## Task 1 — Reliable delivery
- I built **Selective Repeat** (window 8, one 40-step timer per packet). Stop-and-wait has to wait a full round trip after every packet, which looked far too slow for 250 packets, and Go-Back-N resends the whole window when one packet is lost, which looked wasteful.
- The receiver sends an **ACK for every data packet it receives**, duplicate or not. An ACK can get lost, and if the receiver stayed silent on a duplicate the sender would just keep retransmitting forever. Already-received sequence numbers are dropped, and out-of-order packets are buffered until their turn comes.
- For seed 246 the channel actually carried **326 packets** (42 lost, 13 duplicated). The minimum needed is 250, so reliability cost about **1.3x** more. Seed 999 (299 packets) and seed 7 (305 packets) also gave a matching SHA-256.
- **What broke first.** I built a deliberately sloppy receiver (no duplicate removal, no reorder buffer, just append whatever arrives) and turned on one fault at a time. Loss alone broke it (2,280 B arrived): the packet retransmitted after a timeout arrived together with the original, so the data grew. Duplication alone also broke it (2,048 B). Reordering alone happened to work, but only because the sender emits one packet per step, so almost nothing queues on the wire — that does not mean reordering is safe. So **loss and duplication broke it first**, and loss leads to retransmissions, which end up as the duplication problem anyway.
- One more experiment: I made the receiver stay silent for packets it had already received, and on a lossy channel the transfer **never finished** (it used all 200,000 steps and only 168 B arrived with loss alone, 88 B with all three faults on). Once an ACK is lost the sender keeps retransmitting while the receiver silently discards, so it never ends. That is why duplicate data must still be ACKed.

## Task 2 — Looking at my own link
- The first network is **home Wi-Fi** (IP 192.168.219.x), not campus; the second is **phone tethering** (IP 10.148.x.x). The target was a 5 MB download from speed.cloudflare.com, five runs each.

| Network | Throughput median | Min ~ max | Handshake median |
|---|---|---|---|
| home wifi | 147.1 Mbps | 82.8 ~ 151.8 | 13.2 ms |
| tethering | 65.6 Mbps | 54.1 ~ 75.9 | 26.4 ms |

- **A2** I kept only the Cloudflare (162.159.140.220) connections in the capture. For the first connection (port 54700) the SYN is frame 1, SYN-ACK is frame 2 and ACK is frame 3 (in the original full capture the SYN was frame 1438).
- **A3** The initial sequence numbers are 742180953 on my side and 1667337137 on the server's. Neither is 0 and they differ from each other. Starting at 0 would make it easy to confuse a late packet from an earlier connection with the new one, and easy to predict, so the ends seem to choose hard-to-predict values on purpose.
- **A4** My SYN options were MSS 1460, window scale 8 and SACK permitted. The server answered with MSS 1400 and window scale 13. So the real segment size follows the smaller one, 1400.
- **A5** The window I advertised started at 65,280 B and grew to about **2 MB** (2,096,896 B), but the bytes actually in flight peaked at only about **1 MB** (987,000 B). The limit was not the receive window; it was the sender's congestion window (slow start).
- **B4 spread.** On home wifi only the first run was off: 82.8 Mbps with a TTFB of 240 ms, while the other four ran at 147~152 Mbps with a TTFB around 55~60 ms. The first run was probably slower because DNS or the path was cold, but I could not confirm that. Beyond that, contention on the wireless link and other programs' traffic (the capture also had YouTube mixed in) change from run to run, so the numbers wobble a little. Tethering varied more, 54~76 Mbps, because of signal conditions.
- **B5** The handshake time is almost exactly one RTT. A 5 MB transfer is short, so most of it is slow start, and the window doubles every RTT, so **twice the RTT means twice as long to grow to the same size.** Even on a long transfer, throughput is roughly window ÷ RTT, so a longer RTT hurts. Here tethering had about twice the handshake time (26.4 vs 13.2 ms) and about 0.45x the throughput (65.6 vs 147.1 Mbps). The tethering link itself also differs, so RTT alone does not explain everything.

## Task 3 — Beating the fixed window
- The baseline has goodput 986.8, loss 37.4% and an average queue of 8.8. My controller got **goodput 955.2 (97% of the baseline), loss 0.5% and an average queue of 4.4, which is strong**.
- **R5** On goodput alone the baseline is the highest, but it keeps the queue permanently full (average 8.8) and throws away 37% of what it sends. That queue is delay, so every other flow on the same link slows down too, and the dropped packets travelled all the way to the link only to be wasted. It is fast only for itself; for the link as a whole it is the worst sender.
- **What my window converges to.** The link pipe holds about 20 packets (RTT 20 slots × 1 packet per slot) and the queue holds 10, so loss starts above 30. My window climbs to 20 with slow start, then grows +1 per RTT, and on loss it is cut to 0.7x, so it oscillates **roughly between 22 and 31**. With an average queue of 4.4, the average window is about 24~25. That keeps the pipe full while using only a little queue.
- **Gentler backoff.** A 0.6x cut gave goodput 92% with queue 3.8, 0.7x gave 97% with queue 4.4, and 0.85x gave 99% but a queue of 6.7, which **exceeds the limit (5.0) and fails**. The less I cut, the higher goodput goes, but the queue grows by the same amount and other flows have to wait longer.
- Loss can only be detected by timeout (60 slots), and once the pipe jams the timeouts arrive all at once, so after a loss the controller ignores further losses until a window's worth of ACKs has come back.
