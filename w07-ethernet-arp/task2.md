# Task 2 · Watch ARP Happen

**Files** — your own ARP table and a capture you take yourself
**Theory** — §6.4.1 ARP
**Kind** — **hands-on. This one cannot be done from code alone.**

---

## Why this task exists

Tasks 1 and 3 are simulations. ARP is the one protocol in this course you can
break and repair on your own laptop in ten seconds, and watching it refill is
the clearest demonstration of soft state in the whole subject.

## Part A · Empty it and watch it come back

```bash
# look first
arp -a  | tee out/arp-before.txt          # macOS · Linux · Windows

# then empty it - needs administrator rights
sudo arp -a -d                            # macOS
sudo ip -s -s neigh flush all             # Linux
netsh interface ip delete arpcache        # Windows, as Administrator

arp -a                                    # should be nearly empty
ping -c 3 <your gateway>
curl -s -o /dev/null https://www.korea.ac.kr
arp -a  | tee out/arp-after.txt
```

| # | Requirement |
|---|---|
| A1 | `out/arp-before.txt` and `out/arp-after.txt`, taken on your machine |
| A2 | Which entry came back **first**, and why that one |
| A3 | How many entries are in `after` compared with `before`? Explain the difference |
| A4 | You visited a web server on the other side of the world. Is it in the table? Say why not, in terms of what ARP is for |

A4 is the point of the whole task. The table stays small no matter how much of
the internet you talk to, and understanding why is understanding what layer ARP
lives at.

## Part B · Catch the request and the reply

Wireshark, capture filter `arp`, then empty the table again and ping your gateway.
Save as `out/arp.pcapng`.

| # | Requirement |
|---|---|
| B1 | One ARP **request** and its matching **reply** |
| B2 | Report the request's destination MAC. Then the reply's. They are not the same kind of address |
| B3 | Say what each of those two means: who received the request, and who received the reply |
| B4 | Count the ARP traffic in your capture over one minute. Now multiply by the number of machines on a campus segment |

B2 and B3 are the finding: a question everybody has to hear, an answer only one
machine needs. That asymmetry is why ARP scales at all, and B4 is where you see
its limit.

## Pass condition

Both text files and the capture exist, and `out/observation.md` answers
A2–A4 and B2–B4.

```bash
python3 test_tasks.py --task 2
```

## Path (B) · if you cannot get administrator rights

Clearing the ARP cache needs them, and on a managed laptop you may not have them.

- Use the official Ethernet/ARP trace in `traces/` for Part B
- For Part A, you can still run `arp -a` and answer A3 and A4 from what is there —
  say that you could not clear it, and what that means for A2 specifically
  (you are then reading a table someone else's traffic filled, not yours)

## What to write in `observation.md`

- The first entry to come back, and why it had to be that one
- Why a server on the other side of the world is not in your ARP table
- The two destination addresses from B2, and what each one means
