#!/usr/bin/env python3
"""Week 7 · Task 3 — A switch that runs out of room.

Textbook §6.4.3.

A switch does not have room for every station on the network. Its forwarding
table sits in a fixed amount of fast memory, and when that fills, something has
to go. Whatever goes gets **flooded** the next time anyone sends to it - out of
every port, to every station that did not ask for it.

`NaiveSwitch` handles a full table the simplest way: throw out whichever entry
has been there longest. That is a perfectly reasonable first idea and it is
close to the worst thing you can do with this traffic.

    python3 bench.py
    python3 bench.py --yours

Correctness first: every frame whose destination is reachable must still reach
it. A switch that floods less because it delivers less is not a switch.
"""
from collections import OrderedDict


class NaiveSwitch:
    """Correct. Evicts the oldest entry, which is not the least useful one."""

    BROADCAST = "ff:ff:ff:ff:ff:ff"

    def __init__(self, ports, capacity):
        self.ports = ports
        self.capacity = capacity
        self.table = OrderedDict()                 # mac -> port, insertion order

    def handle(self, frame, in_port):
        src, dst, now = frame
        if src not in self.table and len(self.table) >= self.capacity:
            self.table.popitem(last=False)         # throw out the oldest arrival
        self.table[src] = in_port

        if dst == self.BROADCAST or dst not in self.table:
            return [p for p in range(self.ports) if p != in_port]
        out = self.table[dst]
        return [] if out == in_port else [out]


class YourSwitch:
    """Your switch. Same interface, same deliveries, far less flooding.

        __init__(ports, capacity)
        handle((src, dst, time), in_port) -> ports to forward out of

    `self.table` must exist and must never hold more than `capacity` entries.
    The harness checks this after every frame.

    What the baseline gets wrong: it decides what to keep by **when the entry
    arrived**, and that has nothing to do with whether it is about to be needed.
    On this trace a handful of stations carry most of the traffic, and the
    baseline keeps throwing them out to make room for stations that spoke once.

    Two questions worth separating:

      * which entry should leave when the table is full?
      * should learning a new source ever be *declined*?

    The second one is less obvious and is worth thinking about before you
    dismiss it.

    Note what you are NOT allowed to do: you cannot look at `where`, you cannot
    see the future, and you cannot hold more than `capacity` entries. Everything
    you know comes from the frames you have already handled.
    """

    BROADCAST = "ff:ff:ff:ff:ff:ff"

    # Policy: least-frequently-used eviction, plus admission control.
    #   * Every frame that names a MAC (as source or destination) is a "hit".
    #   * When the table is full, the entry with the fewest hits is evicted.
    #   * A new source is only admitted if it has more hits than that victim;
    #     a station heard from once does not push out a busy one.
    # Hit counts are kept for table entries and for a "ghost" list of the most
    # recently seen non-table MACs, the same size as the table, so the
    # bookkeeping stays bounded at 2 x capacity.

    def __init__(self, ports, capacity):
        self.ports = ports
        self.capacity = capacity
        self.table = {}                 # mac -> port
        self.hits = {}                  # mac -> hits, for table entries only
        self.ghost = OrderedDict()      # mac -> hits, for recent non-table MACs

    def _hit(self, mac):
        if mac in self.table:
            self.hits[mac] += 1
        else:
            self.ghost[mac] = self.ghost.pop(mac, 0) + 1
            if len(self.ghost) > self.capacity:
                self.ghost.popitem(last=False)

    def _learn(self, src, in_port):
        if src in self.table:
            self.table[src] = in_port   # newest evidence wins if it moved
            return
        hits = self.ghost.get(src, 1)
        if len(self.table) >= self.capacity:
            victim = min(self.table, key=self.hits.__getitem__)
            if self.hits[victim] >= hits:
                return                  # decline: the newcomer is not worth it
            del self.table[victim]
            self.ghost[victim] = self.hits.pop(victim)
        self.ghost.pop(src, None)
        self.table[src] = in_port
        self.hits[src] = hits

    def handle(self, frame, in_port):
        src, dst, _ = frame
        if dst != self.BROADCAST:
            self._hit(dst)
        self._hit(src)
        self._learn(src, in_port)

        if dst == self.BROADCAST or dst not in self.table:
            return [p for p in range(self.ports) if p != in_port]
        out = self.table[dst]
        return [] if out == in_port else [out]
