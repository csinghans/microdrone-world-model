# search-nroom v1 — does the flat-grid coverage search scale to N rooms?

## Feasibility probe (no bars — this reframes the N-room problem before any gate)

Hans's chosen direction after the two-room GREEN: topological map /
N-room. Before building a topological room graph, the feasibility-first
question: does the EXISTING flat-grid Frontier (which routes over one
undifferentiated safe-cell BFS graph) already scale to several rooms,
or does it break — and if it breaks, HOW?

`sim/indoor/rooms.py:n_room(seed, n_rooms)` — N rooms in a line, N-1
doorways (the two_room brick-divider recipe relocated to each internal
boundary), beacon hidden in the LAST room, each room 3.0 m wide.
Frontier + privileged geometric safety (the ceiling), n=10 each:

| layout | find | success | return\|found | collision | cov | steps_to_find(med) |
|---|---|---|---|---|---|---|
| 3-room (2 doorways) | 1.000 | 0.800 | 0.800 | **0.100** | 0.72 | 166 |
| 4-room (3 doorways) | 1.000 | 0.900 | 0.900 | **0.300** | 0.70 | 222 |

## Finding: it FINDS through N doorways, but it does not THREAD them safely

**Finding scales — the topological map is NOT needed to find across
rooms.** find 1.000 at both 3 and 4 rooms: the flat-grid Frontier hops
through multiple doorways and reaches the far-room beacon every time.
BFS over the safe-cell graph routes multi-doorway paths fine; coverage
and homing already cross several gaps.

**Safe threading does NOT scale.** Collision climbs with doorway count
at FIXED room width — 3-room 0.100 -> 4-room 0.300 (both 3.0 m rooms,
so this is the clean count effect, not a width artifact) — and it does
so even at the GEOMETRIC ceiling, the omni-truth filter that crashed
0.000 in single-room (1a) and two-room. **The doorway is the collision
hotspot, and the risk compounds with the number of doorways.**

**This reframes the N-room direction.** The topological map's real
payload is not finding (solved) but DOORWAY-AWARE SAFE TRAVERSAL:
detect the doorway, approach it centred, thread straight and slow. A
flat grid treats a doorway as ordinary cells and threads it
opportunistically; under PID momentum the body clips a divider brick on
an off-centre approach, and every extra doorway is another roll of that
die. Because even the privileged geometric filter clips, **the problem
is planning/control, not sensing** — the deployable beams8 filter (<=
the geometric ceiling) can only do at least as badly, so there is no
point measuring it until the threading is fixed.

## Honest notes
- n=10 is probe-level (0.100 = 1/10, 0.300 = 3/10); the TREND (crashes
  rise with doorway count at fixed width) is the finding, not the point
  estimates. A gate would need the usual pooled n.
- two_room (3.5 m rooms, one doorway) was collision 0.000; the 0.5 m
  wider room eases the approach, which is itself a hint that the fix is
  about the doorway APPROACH geometry — but the clean, width-controlled
  signal is 3-room vs 4-room (both 3.0 m).
- success < find because a few episodes clip (crash) or run out of the
  (large) return budget; find is unconditional, success needs a clean
  round trip.

## Named next (its own pre-registration)
1. **Doorway-collision diagnostic** — reuse the `on_collision` forensics
   hook (from search_hybrid_v1): are the clips AT the doorway bricks, on
   which leg, executing which action, on a centred or off-centre
   approach? Pinpoint the mechanism before building the fix.
2. **Doorway-aware traversal** — detect a doorway (a gap flanked by near
   returns on the ring), centre up on it, thread straight and slow;
   gate on cutting the multi-doorway collision back toward the two_room
   0.000 at fixed width.
3. **Topological room graph** — only after safe threading: rooms as
   nodes, doorways as edges, for efficient N-room coverage planning (the
   memory-efficient map the <1 MB SRAM budget wants), not for finding.
