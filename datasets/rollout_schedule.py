"""Cross world identity with intervention/passive and classic threat roles.

    python -m datasets.rollout_schedule

World weights remain the explicit cycle, including repeated names. Roles
advance independently on each world's visits; using a single global index
for all three cycles aliases moving to passive in the three-world recipe.
"""

from collections import Counter
from dataclasses import dataclass

LAYOUTS = ("world_balanced", "legacy")


@dataclass(frozen=True)
class RolloutRole:
    world: str
    in_path: bool
    passive: bool


def plan(n_rollouts, worlds, layout="world_balanced"):
    """Deterministic roles with no RNG consumption; legacy replays old recipes.

    Every six visits to a world include four intervention and two passive
    rollouts. Classic also gets all four threat/passive combinations. Short
    or weighted campaigns can end with a partial cycle; no samples are added.
    """
    if layout not in LAYOUTS:
        raise ValueError(f"unknown schedule layout: {layout}")
    if n_rollouts < 1 or not worlds or any(not w for w in worlds):
        raise ValueError("positive rollout count and nonempty world names required")
    visits = Counter()
    roles = []
    for r in range(n_rollouts):
        world = worlds[r % len(worlds)]
        index = r if layout == "legacy" else visits[world]
        roles.append(
            RolloutRole(world, world != "classic" or index % 2 == 0, index % 3 == 2)
        )
        visits[world] += 1
    return roles


def selftest():
    from itertools import permutations

    for worlds in permutations(("classic", "dense", "moving")):
        roles = plan(36, worlds)
        for world in worlds:
            rows = [r for r in roles if r.world == world]
            assert len(rows) == 12 and sum(r.passive for r in rows) == 4
        classic = [r for r in roles if r.world == "classic"]
        assert Counter((r.in_path, r.passive) for r in classic) == {
            (True, False): 4,
            (False, False): 4,
            (True, True): 2,
            (False, True): 2,
        }
    weighted = plan(48, ("dense", "dense", "classic", "moving"))
    assert Counter(r.world for r in weighted) == {
        "dense": 24,
        "classic": 12,
        "moving": 12,
    }
    assert sum(r.passive for r in weighted if r.world == "dense") == 8
    assert sum(not r.in_path for r in weighted if r.world == "classic") == 6
    legacy = plan(60, ("classic", "dense", "moving"), "legacy")
    assert all(r.passive == (r.world == "moving") for r in legacy)
    assert plan(30, ("classic",), "legacy") == plan(30, ("classic",))
    for i, role in enumerate(plan(31, ("moving", "classic"), "legacy")):
        assert role.passive == (i % 3 == 2)
        assert role.in_path == (role.world != "classic" or i % 2 == 0)
    for args in ((0, ("classic",)), (3, ()), (3, ("classic",), "bad")):
        try:
            plan(*args)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid schedule accepted")
    print(
        "ROLLOUT-SCHEDULE OK: crossed roles, world permutations/weights, legacy parity"
    )


if __name__ == "__main__":
    selftest()
