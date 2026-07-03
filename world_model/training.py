"""Train the nano world model — V-JEPA style, latent prediction, never pixels.

A *world model* answers "if I see this and take this action, what will I see
next?" The trap is to answer in pixels — slow, and it hallucinates detail a
drone can't act on. Here the predictor forecasts the next *latent embedding*,
with the target produced by an EMA copy of the encoder (stop-gradient) and a
variance guard against collapse (see `world_model.losses`).

Why counterfactual labels? A planner never asks "was the action I flew
safe?" — it asks "which of my options is safest *from here*?" Executed
rollouts answer the first question densely and the second only at segment
switches (measured: collision AUC 0.9 but veer-ranking at chance). So the
collision heads are additionally supervised with the simulator's
counterfactual oracle at every frame. Two honesty rules keep the metrics
trustworthy:

  * The train/val split is **by rollout**, not by frame — neighbouring frames
    are near-duplicates, and a random frame split inflates AUC.
  * The **veer-ranking check** grades the one ability planners rely on: on
    held-out frames where geometry says one veer is truly safer, does the
    model rank it safer? Chance = 0.5.

Honest scope: the real V-JEPA is a billion-parameter ViT for Orin-class
boards. This is a *nano distillation of the idea*, sized for a 512 KB int8
budget.
"""

import os

import numpy as np
import torch
import torch.nn as nn

from datasets.intervention_labels import HORIZONS, counterfactual_labels, window_valid
from planner.action_set import A_NORM, ACTION_NAMES, ACTION_VECS, FORWARD
from sim.envs import CTRL_HZ
from sim.scenarios import DANGER_R, FOV_HALF_DEG, RADII
from world_model.collision_head import CollisionHeads, DangerNowHead
from world_model.encoder import Encoder
from world_model.losses import augment_torch, ema_update, roc_auc, variance_guard
from world_model.predictor import MultiPredictor
from world_model.temporal import K_WIN, TemporalEncoder

LAMBDA_VAR = 1.0  # anti-collapse (VICReg-style variance hinge)
LAMBDA_COL = 1.0  # executed-action collision-head weight (real flown future)
LAMBDA_CF = 1.0  # counterfactual collision weight (the ranking supervision)
LAMBDA_NOW = 0.5  # danger-now head weight (the reactive baseline signal)
GAP8_BUDGET_KB = 512
MODEL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "world_model.pth",
)
MODEL_GRU = MODEL.replace(".pth", "_gru.pth")


def _index_samples(data: dict) -> tuple:
    """All (rollout, t) pairs whose command was held over the full H_MAX window,
    with per-horizon, per-ring collision labels of the *flown* future."""
    R, L = data["frames"].shape[:2]
    idx, c_h = [], []
    for r in range(R):
        for t in range(L - HORIZONS[-1]):
            if not window_valid(data["seg"][r], t, HORIZONS[-1]):
                continue
            d = data["dists"][r]
            idx.append((r, t))
            c_h.append(
                [
                    [float(d[t : t + k + 1].min() < rad) for rad in RADII]
                    for k in HORIZONS
                ]
            )
    return np.array(idx, dtype=np.int64), np.array(c_h, dtype=np.float32)


def _split_rollouts(data: dict, rng: np.random.Generator) -> tuple:
    """Rollout-level split, stratified over (world x in-path x passive) so
    val always holds every scenario kind — in particular a passive in-path
    pass (danger-now positives) and, in v0.2 datasets, every world."""
    R = data["frames"].shape[0]
    worlds = (
        np.asarray(data["world_id"])
        if "world_id" in data
        else np.zeros(R, dtype=np.int16)
    )
    tr, va = [], []
    for w in sorted({int(x) for x in worlds}):
        for flag_ip in (True, False):
            for flag_passive in (True, False):
                rolls = [
                    r
                    for r in range(R)
                    if int(worlds[r]) == w
                    and bool(data["in_path"][r]) == flag_ip
                    and (int(data["seg"][r].max()) == 0) == flag_passive
                ]
                if not rolls:
                    continue
                rng.shuffle(rolls)
                n_val = max(1, round(0.2 * len(rolls)))
                va += rolls[:n_val]
                tr += rolls[n_val:]
    return sorted(tr), sorted(va)


def veer_ranking(data: dict, rolls, enc, pred, cheads, device, tgru=None) -> tuple:
    """The action-conditioning acceptance check, scored against a *geometric*
    ground truth. On held-out cruise frames, roll each veer command forward
    kinematically for the longest horizon and measure the true minimum
    clearance either way (privileged pillar layout — used to *evaluate* the
    model, never to control the drone). Keep only the decision-relevant
    frames that vision can actually answer: one veer would cross the danger
    radius and the other would stay clear (by a >0.12 m margin), *and* the
    threatening pillar sits inside the camera FOV. The model is correct when
    it ranks the truly-safer veer as safer. Chance = 0.5."""
    tau1 = np.arange(HORIZONS[-1] + 1) / CTRL_HZ  # (k+1,)
    i_l, i_r = ACTION_NAMES.index("veer_left"), ACTION_NAMES.index("veer_right")
    cos_fov = np.cos(np.radians(FOV_HALF_DEG))
    frames, gt_left_safer, svs = [], [], []
    L = data["frames"].shape[1]
    all_vel = data["pillar_vel"] if "pillar_vel" in data else None
    for r in rolls:
        pil = data["pillars"][r]
        mask = ~np.isnan(pil[:, 0])
        pil = pil[mask]
        if not len(pil):
            continue
        vp = np.asarray(all_vel[r])[mask] if all_vel is not None else np.zeros_like(pil)
        sv = float(data["speed"][r])  # judge each rollout at its own pace
        for t in range(L):
            if data["act_id"][r, t] != FORWARD:
                continue
            p0 = data["pos"][r, t, :2]
            pil_at = pil + (t / CTRL_HZ) * vp  # where the pillars are NOW
            d_v, q_v = [], []
            for i in (i_l, i_r):
                rel_v = sv * ACTION_VECS[i][:2] - vp  # (P, 2) relative motion
                diff = (p0 - pil_at)[None, :, :] + tau1[:, None, None] * rel_v[None]
                dmat = np.linalg.norm(diff, axis=2)  # (k+1, P)
                d_v.append(float(dmat.min()))
                q_v.append(pil_at[dmat.min(axis=0).argmin()])
            d_l, d_r = d_v
            if not (
                abs(d_l - d_r) > 0.12 and min(d_l, d_r) < DANGER_R <= max(d_l, d_r)
            ):
                continue
            rel = (q_v[0] if d_l < d_r else q_v[1]) - p0  # the threatening pillar
            if rel[0] <= float(np.linalg.norm(rel)) * cos_fov:
                continue  # threat outside the camera FOV: unanswerable from vision
            if tgru is None:
                frames.append(data["frames"][r, t])
            else:  # the memory model judges from its K-frame window
                ws = [
                    data["frames"][r, max(t - K_WIN + 1 + j, 0)] for j in range(K_WIN)
                ]
                frames.append(np.stack(ws))
            gt_left_safer.append(d_l > d_r)
            svs.append(sv)
    if not frames:
        return float("nan"), 0
    x = torch.tensor(np.array(frames), dtype=torch.float32, device=device)
    if tgru is None:
        x = x.permute(0, 3, 1, 2) / 255.0
    else:
        n_probe = x.shape[0]
        x = x.reshape(-1, *x.shape[2:]).permute(0, 3, 1, 2) / 255.0
    sv_col = np.array(svs, dtype=np.float32)[:, None]
    a_l = torch.tensor(sv_col * ACTION_VECS[i_l] / A_NORM, device=device)
    a_r = torch.tensor(sv_col * ACTION_VECS[i_r] / A_NORM, device=device)
    with torch.no_grad():
        if tgru is None:
            z = enc(x)
            zb = z
        else:
            z_seq = enc(x).reshape(n_probe, K_WIN, -1)
            z = tgru(z_seq)
            zb = z_seq[:, -1]  # residual base: the current frame
        p_l = torch.sigmoid(cheads(pred(z, a_l, base=zb))[:, -1, 0])  # warn @667ms
        p_r = torch.sigmoid(cheads(pred(z, a_r, base=zb))[:, -1, 0])
    gt = torch.tensor(np.array(gt_left_safer), device=device)
    correct = torch.where(gt, p_l < p_r, p_r < p_l)
    return float(correct.float().mean()), len(frames)


def train(
    data: dict,
    epochs: int = 80,
    batch: int = 64,
    seed: int = 0,
    robust: bool = False,
    temporal: bool = False,
) -> tuple:
    """Train the nano world model on a sequence-format dataset dict and return
    (checkpoint dict, metrics dict). `robust=True` adds appearance
    augmentation to the online encoder's frames (pair it with a `--randomize`
    dataset to close the priced sim-to-real gap). `temporal=True` puts a GRU
    over the last K_WIN frame latents and feeds its state to the predictor
    and every head — memory inside the model (v3 checkpoints); the JEPA
    target stays frame-level, so the memory must earn its keep by predicting
    plain future frames better."""
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)

    idx, c_h = _index_samples(data)
    tr_rolls, va_rolls = _split_rollouts(data, rng)
    tr = np.where(np.isin(idx[:, 0], tr_rolls))[0]
    va = np.where(np.isin(idx[:, 0], va_rolls))[0]
    print(
        f"[INFO] training on {device}: {len(tr)} train / {len(va)} val samples "
        f"({len(tr_rolls)}/{len(va_rolls)} rollouts)"
    )

    R, L = data["frames"].shape[:2]
    flat = torch.tensor(data["frames"].reshape(R * L, *data["frames"].shape[2:]))
    flat = flat.to(device)  # uint8 on device; per-batch floats below
    acts = torch.tensor(data["actions"].reshape(R * L, 4) / A_NORM).to(device)
    c_h_t = torch.tensor(c_h).to(device)
    base = torch.tensor(idx[:, 0] * L + idx[:, 1]).to(device)
    offs = torch.tensor([int(k) for k in HORIZONS]).to(device)
    # the counterfactual oracle: labels for every (frame, candidate, horizon,
    # ring) — valid at every step, so it uses ALL train-rollout frames
    n_a, n_h, n_r = len(ACTION_VECS), len(HORIZONS), len(RADII)
    cf_np, vis_np = counterfactual_labels(data)
    cf_np = cf_np.reshape(R * L, n_a, n_h, n_r).astype(np.float32)
    vis_np = vis_np.reshape(R * L, n_a).astype(np.float32)
    cf = torch.tensor(cf_np).to(device)
    vis = torch.tensor(vis_np).to(device)
    now_all = torch.tensor(
        (data["dists"].reshape(R * L) < DANGER_R).astype(np.float32)
    ).to(device)
    tr_frames = np.array([r * L + t for r in tr_rolls for t in range(L)])
    c_all = torch.tensor(tr_frames).to(device)
    # frames where the *visible* candidate labels disagree carry the ranking
    # signal; most frames are far from any pillar and teach nothing about
    # choice, so half of every counterfactual batch oversamples the former
    cfv = (cf_np * vis_np[:, :, None, None])[tr_frames].reshape(
        len(tr_frames), n_a, n_h * n_r
    )
    disagree = (cfv.max(axis=1) != cfv.min(axis=1)).any(axis=1)
    c_hard = torch.tensor(tr_frames[disagree] if disagree.any() else tr_frames).to(
        device
    )
    cands = torch.tensor(ACTION_VECS / A_NORM).to(device)

    def frames_at(flat_idx):  # uint8 (N,64,64,3) -> float (N,3,64,64)
        return flat[flat_idx].permute(0, 3, 1, 2).float() / 255.0

    enc, tgt = Encoder().to(device), Encoder().to(device)
    tgt.load_state_dict(enc.state_dict())
    for p in tgt.parameters():
        p.requires_grad_(False)
    pred = MultiPredictor().to(device)
    cheads = CollisionHeads().to(device)
    nhead = DangerNowHead().to(device)
    tgru = TemporalEncoder().to(device) if temporal else None

    k_offs = torch.arange(K_WIN - 1, -1, -1, device=device)

    def state_at(flat_idx, aug: bool):
        """Frames -> the model's decision state. Static: z_t. Temporal: the
        GRU over the last K_WIN frame latents, windows clamped at the
        rollout start (early frames repeat the first). Returns (state,
        z_last) — z_last feeds the variance guard and the no-op baseline,
        which stay frame-level by design."""
        if not temporal:
            x = frames_at(flat_idx)
            z = enc(augment_torch(x) if aug else x)
            return z, z
        start = (flat_idx // L) * L
        win = torch.maximum(
            flat_idx.unsqueeze(1) - k_offs.unsqueeze(0), start.unsqueeze(1)
        )
        x = frames_at(win.reshape(-1))
        z = enc(augment_torch(x) if aug else x).reshape(len(flat_idx), K_WIN, -1)
        return tgru(z), z[:, -1]

    params = (
        list(enc.parameters())
        + list(pred.parameters())
        + list(cheads.parameters())
        + list(nhead.parameters())
        + (list(tgru.parameters()) if temporal else [])
    )
    opt = torch.optim.Adam(params, lr=1e-3)
    bce = nn.BCEWithLogitsLoss()
    bce_none = nn.BCEWithLogitsLoss(reduction="none")

    for _epoch in range(1, epochs + 1):
        enc.train(), pred.train(), cheads.train(), nhead.train()
        order = tr[torch.randperm(len(tr)).numpy()]
        for i in range(0, len(order), batch):
            b = torch.tensor(order[i : i + batch]).to(device)
            opt.zero_grad()
            h_t, z_last = state_at(base[b], robust)
            z_hat = pred(h_t, acts[base[b]], base=z_last)  # (B,H,D)
            with torch.no_grad():
                z_tgt = torch.stack(
                    [tgt(frames_at(base[b] + k)) for k in offs], dim=1
                )  # (B,H,D)
            pred_loss = ((z_hat - z_tgt) ** 2).mean()
            var_loss = variance_guard(z_last)
            col_loss = bce(cheads(z_hat), c_h_t[b])
            # counterfactual batch: half random frames, half decision-relevant
            half = max(1, len(b) // 2)
            cb = torch.cat(
                [
                    c_all[torch.randint(len(c_all), (half,), device=device)],
                    c_hard[torch.randint(len(c_hard), (half,), device=device)],
                ]
            )
            z_c, z_c_last = state_at(cb, robust)
            z_cf = pred(
                z_c.repeat_interleave(n_a, dim=0),
                cands.repeat(len(z_c), 1),
                base=z_c_last.repeat_interleave(n_a, dim=0),
            )
            w = vis[cb].reshape(-1, 1, 1)  # unanswerable (frame, cand): no loss
            cf_loss = (
                bce_none(cheads(z_cf), cf[cb].reshape(-1, n_h, n_r)) * w
            ).sum() / (w.sum() * n_h * n_r + 1e-6)
            # danger-now stays frame-level: it is the honest REACTIVE baseline,
            # and a baseline that borrows the memory stops being one
            now_loss = bce(nhead(z_c_last), now_all[cb])
            (
                pred_loss
                + LAMBDA_VAR * var_loss
                + LAMBDA_COL * col_loss
                + LAMBDA_CF * cf_loss
                + LAMBDA_NOW * now_loss
            ).backward()
            opt.step()
            ema_update(tgt, enc)

    # -- validation metrics (rollout-level split, so these are honest) --------
    enc.eval(), pred.eval(), cheads.eval(), nhead.eval()
    if temporal:
        tgru.eval()
    vb = torch.tensor(va).to(device)
    with torch.no_grad():
        z_t, z_val_last = state_at(base[vb], False)
        z_hat = pred(z_t, acts[base[vb]], base=z_val_last)
        z_tgt = torch.stack([tgt(frames_at(base[vb] + k)) for k in offs], dim=1)
        mse_h = ((z_hat - z_tgt) ** 2).mean(dim=(0, 2)).cpu().numpy()
        noop_h = (
            ((z_val_last.unsqueeze(1) - z_tgt) ** 2).mean(dim=(0, 2)).cpu().numpy()
        )  # predictor does nothing: "the future frame looks like this frame"
        scores = torch.sigmoid(cheads(z_hat)).cpu().numpy()[:, :, 0]  # warn ring
    auc_h = [roc_auc(scores[:, i], c_h[va][:, i, 0]) for i in range(len(HORIZONS))]
    # v0.2: the slice that matters — AUC@32 per world kind, when worlds exist
    auc_by_world = {}
    if "world_id" in data:
        names = {0: "classic", 1: "dense", 2: "moving"}
        sw = np.asarray(data["world_id"])[idx[va][:, 0]]
        for w in sorted({int(x) for x in sw}):
            m = sw == w
            if int(m.sum()) >= 20:
                auc_by_world[names.get(w, str(w))] = roc_auc(
                    scores[m][:, -1], c_h[va][m][:, -1, 0]
                )
    # danger-now needs no held future window, so score it on *every* val frame
    now_idx = torch.tensor([r * L + t for r in va_rolls for t in range(L)]).to(device)
    now_lbl = np.array(
        [float(data["dists"][r, t] < DANGER_R) for r in va_rolls for t in range(L)],
        dtype=np.float32,
    )
    with torch.no_grad():
        now_scores = (
            torch.cat(
                [
                    torch.sigmoid(nhead(state_at(now_idx[i : i + 512], False)[1]))
                    for i in range(0, len(now_idx), 512)
                ]
            )
            .cpu()
            .numpy()
        )
    now_auc = roc_auc(now_scores, now_lbl)
    side, n_side = veer_ranking(data, va_rolls, enc, pred, cheads, device, tgru=tgru)
    if n_side < 20:  # tiny val sets may lack decision-relevant geometry; the
        # probe never trains on labels, so widening it stays meaningful
        side, n_side = veer_ranking(
            data, range(data["frames"].shape[0]), enc, pred, cheads, device, tgru=tgru
        )
        print("[INFO] veer-ranking widened to all rollouts (val had too few frames)")

    n_params = sum(p.numel() for p in params)
    ckpt = {
        "encoder": enc.state_dict(),
        "predictor": pred.state_dict(),
        "collision_heads": cheads.state_dict(),
        "now_head": nhead.state_dict(),
        **({"temporal": tgru.state_dict()} if temporal else {}),
        "meta": {
            "version": 3 if temporal else 2,
            "D": int(z_t.shape[1]),
            "A": int(acts.shape[1]),
            "horizons": [int(k) for k in HORIZONS],
            "radii": [float(rad) for rad in RADII],
            "danger_r": float(DANGER_R),
            "a_norm": [float(v) for v in A_NORM],
            "action_names": list(ACTION_NAMES),
            "action_vecs": [[float(v) for v in row] for row in ACTION_VECS],
        },
    }
    metrics = {
        "mse": mse_h,
        "noop": noop_h,
        "auc": auc_h,
        "auc_by_world": auc_by_world,
        "now_auc": now_auc,
        "side": side,
        "n_side": n_side,
        "int8_kb": n_params / 1024,  # weights only; the eval reports the full budget
        "n_train": len(tr),
        "n_val": len(va),
    }
    return ckpt, metrics


def load_model(path: str = MODEL, device: str = "cpu"):
    """Rebuild the trained nets from a checkpoint. Returns
    (encoder, predictor, collision_heads, now_head, meta), all in eval mode.
    v3 (temporal) checkpoints attach the GRU as `encoder.temporal` — every
    consumer keeps its signature, and stateful policies check for it."""
    ckpt = torch.load(path, map_location=device, weights_only=True)
    meta = ckpt["meta"]
    if meta.get("version") not in (2, 3):
        raise SystemExit(f"{path} is not a v2/v3 checkpoint; re-train first.")
    enc, pred = Encoder().to(device), MultiPredictor().to(device)
    cheads, nhead = CollisionHeads().to(device), DangerNowHead().to(device)
    enc.load_state_dict(ckpt["encoder"])
    pred.load_state_dict(ckpt["predictor"])
    cheads.load_state_dict(ckpt["collision_heads"])
    nhead.load_state_dict(ckpt["now_head"])
    mods = [enc, pred, cheads, nhead]
    if "temporal" in ckpt:
        tgru = TemporalEncoder().to(device)
        tgru.load_state_dict(ckpt["temporal"])
        enc.temporal = tgru  # registered submodule: budgets count it too
        mods.append(tgru)
    for m in mods:
        m.eval()
    return enc, pred, cheads, nhead, meta
