#!/usr/bin/env python3
"""Week 6 · Task 3 — Reconverge without recomputing the world.

Textbook §5.2.1, §5.3.

A link flaps. Every router in the area has to decide what changed. `FullRecompute`
does the honest thing: throw the table away and run Dijkstra again, from scratch,
for every event. It is correct and it is what the first implementations did.

It is also why a single flapping link in a large area used to melt the CPU of
every router that could see it.

Beat it:

    python3 bench.py
    python3 bench.py --yours

Correctness first. `bench.py` compares your table against a full recompute after
**every single event**. A router that is fast and wrong black-holes traffic.
"""
import heapq

# The harness counts how many times you run a full SPF. This is the score:
# wall-clock time in Python says more about dictionary overhead than about
# routing, but "how many times did the CPU have to recompute the world" is
# exactly what melted real routers.
SPF_RUNS = 0


def dijkstra_table(graph, source, with_dist=False):
    """Reference shortest-path-first. Returns {destination: first_hop}.

    Use THIS function whenever you need a full recompute. Rolling your own to
    dodge the counter is not an optimisation, it is cheating the meter.
    """
    global SPF_RUNS
    SPF_RUNS += 1
    best = {source: (0, None)}
    pq, done = [(0, source, None)], set()
    while pq:
        cost, node, first_hop = heapq.heappop(pq)
        if node in done:
            continue
        done.add(node)
        best[node] = (cost, first_hop)
        for nbr, w in sorted(graph[node].items()):
            if nbr in done:
                continue
            hop = nbr if node == source else first_hop
            if cost + w < best.get(nbr, (float("inf"), None))[0]:
                best[nbr] = (cost + w, hop)
                heapq.heappush(pq, (cost + w, nbr, hop))
    table = {d: h for d, (_, h) in best.items() if d != source and h}
    if with_dist:                       # same run, same counter - just also hand back the costs
        return table, {d: c for d, (c, _) in best.items()}
    return table


class FullRecompute:
    """On every event, forget everything and run SPF again."""

    def __init__(self, graph, source):
        self.graph = {n: dict(e) for n, e in graph.items()}
        self.source = source
        self.table = dijkstra_table(self.graph, source)

    def link_change(self, a, b, cost):
        """cost=None means the link went down."""
        if cost is None:
            self.graph[a].pop(b, None)
            self.graph[b].pop(a, None)
        else:
            self.graph[a][b] = cost
            self.graph[b][a] = cost
        self.table = dijkstra_table(self.graph, self.source)


INF = float("inf")


class YourRouter:
    """Keeps, between events, the cost to every node (`dist`) and which
    neighbour-of-the-tree each node hangs from (`parent`). `table` is derived
    from the parent tree: a node's first hop is its parent's first hop.

    What one event can do to the edge a-b, looking at each direction p -> n:

      * improves  dist[p] + cost < dist[n]            -> dist drops for n and
        whatever hangs below it: propagate the drop only through the nodes that
        actually get closer (`_relax_from`), not a full SPF
      * parent p of n is lost (down / costlier)       -> look for another edge
        that is still tight for n. If there is one, dist is unchanged and only
        the parent (and the hops below it) move. If there is none, n really got
        further away: full SPF.
      * becomes a new tight edge (equal cost)         -> only matters if it wins
        the tie-break against the current parent
      * anything else                                 -> nothing to do

    Tie-break (same as dijkstra_table, so the tables are identical): among the
    edges that give n its shortest cost, the one whose far end is settled first,
    i.e. the smaller (dist, name).
    """

    def __init__(self, graph, source):
        self.graph = {n: dict(e) for n, e in graph.items()}
        self.source = source
        self._spf()

    def _spf(self):
        self.table, self.dist = dijkstra_table(self.graph, self.source, with_dist=True)
        self.parent = {n: self._best_parent(n) for n in self.dist if n != self.source}

    def _best_parent(self, n):
        dist, d = self.dist, self.dist[n]
        preds = [p for p, w in self.graph[n].items() if dist.get(p, INF) + w == d]
        return min(preds, key=lambda p: (dist[p], p)) if preds else None

    def _relax_from(self, n, d):
        """Node n can now be reached at cost d < dist[n]. Push the improvement
        outward, touching only nodes that really get cheaper."""
        dist, graph, touched = self.dist, self.graph, set()
        pq = [(d, n)]
        while pq:
            c, x = heapq.heappop(pq)
            if c >= dist.get(x, INF):
                continue
            dist[x] = c
            touched.add(x)
            for y, w in graph[x].items():
                if c + w < dist.get(y, INF):
                    heapq.heappush(pq, (c + w, y))
        # a closer node can also create a new equal-cost option for its neighbours
        around = set(touched)
        for x in touched:
            around.update(y for y in graph[x] if y in dist)
        for x in around:
            if x != self.source:
                self.parent[x] = self._best_parent(x)
        self._hops_from_parents()

    def _hops_from_parents(self):
        table, src = {}, self.source
        for n in sorted(self.parent, key=lambda n: self.dist[n]):
            p = self.parent[n]
            table[n] = n if p == src else table[p]
        self.table = table

    def link_change(self, a, b, cost):
        old = self.graph[a].get(b)
        if cost is None:
            self.graph[a].pop(b, None)
            self.graph[b].pop(a, None)
        else:
            self.graph[a][b] = cost
            self.graph[b][a] = cost
        if old == cost:
            return
        dist, moved = self.dist, False
        if cost is not None:
            for p, n in ((a, b), (b, a)):
                if p in dist and dist[p] + cost < dist.get(n, INF):
                    return self._relax_from(n, dist[p] + cost)   # shorter path appears
        for p, n in ((a, b), (b, a)):
            if p not in dist:                       # p unreachable: edge is irrelevant
                continue
            dn = dist.get(n, INF)
            if n == self.source:
                continue
            if old is not None and dist[p] + old == dn and self.parent[n] == p:
                new = self._best_parent(n)          # lost the edge n hung from
                if new is None:
                    return self._spf()              # no other way: n got further
                self.parent[n], moved = new, True
            elif cost is not None and dist[p] + cost == dn:
                cur = self.parent[n]                # new equal-cost edge for n
                if (dist[p], p) < (dist[cur], cur):
                    self.parent[n], moved = p, True
        if moved:
            self._hops_from_parents()
