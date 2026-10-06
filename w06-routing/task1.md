# Task 1 · Link State by Hand

**File** — `task1_linkstate.py`
**Theory** — §5.2.1 link-state routing, §5.3 OSPF
**Kind** — implementation · fully offline

---

## What you are building

Every OSPF router in an area ends up holding the same map. Then each one computes,
alone, where to send a packet for every destination. The computation is Dijkstra.
The output is **one next hop per destination** — not a path.

That last part is what lets routing work without anyone carrying a route inside
the packet, and it is the part that is easy to get subtly wrong.

## Requirements

| # | Requirement |
|---|---|
| R1 | `dijkstra(graph, source)` returns `{node: cost}`, unreachable nodes absent |
| R2 | `forwarding_table(graph, source)` returns `{destination: first_hop}` |
| R3 | Every `first_hop` must be a **direct neighbour** of `source` |
| R4 | The source itself is not in its own table |
| R5 | Cutting a link must change the table when it should. The harness cuts `u-x` |
| R6 | `heapq` is allowed. `networkx` is not |

## The trap in R2

It is easy to compute the whole path and return `path[1]`. That works. But decide
what you do when **two shortest paths tie** — a real router has to pick one, and
which one it picks determines whether traffic is split or pinned. Say what rule
you used in `observation.md`.

Note also that in `TOPOLOGY` the direct link `u-w` costs 5, but `u-x-y-w` costs 3.
The shortest path is not the direct one. If your table sends `w` traffic out the
`w` interface, you computed adjacency, not routing.

## Pass condition

```bash
python3 task1_linkstate.py --verify
```

Ten checks: the cost vector from `u`, the forwarding table at `u`, that every
node's table covers every destination with a real neighbour as the hop, and that
`u` reroutes when `u-x` fails.

```
  all ok
```

## What to write in `observation.md`

- Your tie-breaking rule for equal-cost paths, and what a real router does
- `u`'s next hop for `w`, and why it is not `w`
- After `u-x` fails, which destinations changed hop and which did not
