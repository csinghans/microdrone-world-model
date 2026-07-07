"""Phase 1b step 1 — the transfer probe (feasibility-first).

Does the shipped, TRANSIT-trained world model produce a useful
collision signal in SEARCH rooms for the TRANSLATIONAL nav actions?
Fly the green geometric frontier and, alongside, tap the WM's warn
probability for the executed nav action each decision; score whether
that probability rises before true low-clearance events.

Frozen read (experiments/search_wm_v1/journal.md): AUC >= 0.75 on
forward AND >= 0.65 pooled -> the transit WM transfers, build the
vision filter on it; AUC < 0.6 pooled -> retrain required first.

Run:
  python -m eval.eval_search_wm_probe --n 12
  python -m eval.eval_search_wm_probe --selftest
"""

import argparse
import sys

import numpy as np

from eval.search_episode import _safe_action
from planner.latent_mpc import DECIDE_EVERY, _frame_tensor
from planner.nav_action_set import NAV_ACTION_VECS, nav_menu
from sim.envs import START, VelCommander, grab_frame, make_ctrl
from sim.search_scenario import remove_bodies

WARN_HORIZON_ANY = True  # use the max warn prob over horizons (any-horizon threat)
LOOKAHEAD_K = 4  # a "true near" decision = clearance dips below the ring within K
# the WM's warn ring is 0.7 m; ask whether its warn-prob predicts truly being
# within 0.7 m of a surface. (SAFE_MARGIN=0.35 never fires — the geometric
# filter keeps clearance above it by construction, so nothing to predict.)
DANGER_CLEAR = 0.7


def _auc(scores, labels):
    """Rank-based AUC (Mann-Whitney); 0.5 if degenerate."""
    s, y = np.asarray(scores, float), np.asarray(labels, int)
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(s)
    ranks = np.empty(len(s), float)
    ranks[order] = np.arange(1, len(s) + 1)
    r_pos = ranks[y == 1].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def probe(
    n=12, seed0=130000, max_decisions=1500, speed=0.6, ckpt=None, fov_label=False
):
    import torch

    from search.strategies import get_strategy
    from sim.envs import make_env
    from sim.indoor.rooms import single_room

    if ckpt:  # a specific (e.g. retrained-on-rooms) checkpoint
        from world_model.training import load_model

        enc, pred, cheads, _nhead, meta = load_model(ckpt, device="cpu")
    else:
        from eval.eval_closed_loop import load_or_train

        enc, pred, cheads, _nhead, meta = load_or_train(device="cpu")
    a_norm = np.array(meta["a_norm"], dtype=np.float32)
    cands = torch.tensor(NAV_ACTION_VECS * speed / a_norm, dtype=torch.float32)

    def warn_prob(frame, action_id):
        with torch.no_grad():
            z = enc(_frame_tensor(frame))
            z_hat = pred(z.expand(len(cands), -1), cands, base=z.expand(len(cands), -1))
            p = torch.sigmoid(cheads(z_hat)).numpy()  # (n_act, H, 2)
        warn = p[action_id, :, 0]
        return float(warn.max() if WARN_HORIZON_ANY else warn[-1])

    env = make_env()
    rows = []  # (warn_prob, action_id, clearance_now)
    clears = []  # per-episode clearance sequences, to build the lookahead label
    for i in range(n):
        sc = single_room(seed0 + i)
        pol = get_strategy("frontier")
        pol.begin(sc)
        obs, _ = env.reset(seed=int(seed0 + i))
        cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
        cmd.reset(obs[0][0:3])
        sx, sy = sc.start_xy
        body_ids = sc.spawn_bodies(env, offset=(sx - START[0], sy - START[1]))
        state = obs[0]
        ep = []
        for _d in range(max_decisions):
            rpos = (
                float(state[0]) + sx - START[0],
                float(state[1]) + sy - START[1],
            )
            if sc.found(rpos):
                break  # probe the SEARCH leg (vision-relevant); stop at found
            frame = grab_frame(env)
            a = pol.decide(
                {
                    "pos": rpos,
                    "sense": None,
                    "ranges": sc.range_sensors(rpos),
                    "step": _d,
                }
            )
            a = _safe_action(sc, rpos, a)
            wp = warn_prob(frame, a)
            # FOV-honest label: score against forward-cone clearance (what
            # the camera can see), the target an FOV-honest WM was trained
            # on; else omnidirectional clearance (the step-1 transit probe)
            clr = sc.forward_clearance(rpos) if fov_label else sc.clearance(rpos)
            ep.append((wp, a, clr))
            for _ in range(DECIDE_EVERY):
                obs, _, _, _, _ = env.step(
                    cmd.rpm(state, speed * NAV_ACTION_VECS[a]).reshape(1, 4)
                )
                state = obs[0]
        remove_bodies(env, body_ids)
        rows.extend(ep)
        clears.append([c for _, _, c in ep])
    env.close()

    # label each decision: does true clearance dip below SAFE_MARGIN within K?
    scores, labels, acts = [], [], []
    idx = 0
    for seq in clears:
        for t in range(len(seq)):
            window = seq[t : t + 1 + LOOKAHEAD_K]
            labels.append(int(min(window) < DANGER_CLEAR))
            scores.append(rows[idx][0])
            acts.append(rows[idx][1])
            idx += 1
    scores, labels, acts = np.array(scores), np.array(labels), np.array(acts)
    fwd = nav_menu()[0]
    fwd_mask = acts == fwd
    return {
        "n_decisions": len(scores),
        "danger_rate": float(labels.mean()),
        "auc_all": _auc(scores, labels),
        "auc_forward": _auc(scores[fwd_mask], labels[fwd_mask]),
        "auc_nav_nonfwd": _auc(scores[~fwd_mask], labels[~fwd_mask]),
        "n_forward": int(fwd_mask.sum()),
    }


def selftest() -> None:
    # AUC math: a perfect separator scores 1.0, a random one ~0.5
    assert abs(_auc([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]) - 1.0) < 1e-9
    assert abs(_auc([0.9, 0.8, 0.2, 0.1], [0, 0, 1, 1]) - 0.0) < 1e-9
    assert np.isnan(_auc([0.5, 0.6], [0, 0]))
    print("SEARCH-WM-PROBE OK: AUC math (perfect 1.0, inverted 0.0, degenerate nan)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed0", type=int, default=130000)
    ap.add_argument(
        "--ckpt", default=None, help="WM checkpoint to probe (else the champion)"
    )
    ap.add_argument(
        "--fov-label", action="store_true", help="score vs forward-cone clearance"
    )
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    r = probe(args.n, args.seed0, ckpt=args.ckpt, fov_label=args.fov_label)
    print(
        f"[wm-probe] decisions {r['n_decisions']} (danger {r['danger_rate']:.2f}) | "
        f"AUC all {r['auc_all']:.3f}  forward {r['auc_forward']:.3f} "
        f"(n={r['n_forward']})  nav-nonfwd {r['auc_nav_nonfwd']:.3f}"
    )


if __name__ == "__main__":
    sys.exit(main())
