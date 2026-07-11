"""Fetch the measured champions a fresh clone cannot train in an afternoon.

    python -m scripts.fetch_champions            # download + verify all
    python -m scripts.fetch_champions --check    # verify what's on disk

Champion checkpoints and policy zips are deliberately git-ignored (they
are *measured artifacts*, not source). They live as GitHub Release
assets instead, pinned by `artifacts.lock.json`: every download is
sha256-verified against the lock, and the lock's hashes were
cross-checked against the campaigns' own results.json records at upload
time. No token needed — the repo is public and downloads go over plain
HTTPS (`urllib`), so this works on a fresh machine with no gh CLI.

Without these files: `--dry` gates still work everywhere (they train
tiny stand-ins), but real campaigns hard-fail on their zero-shot knobs
by design — a missing champion must never be silently substituted.
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(ROOT, "artifacts.lock.json")
BASE = "https://github.com/csinghans/microdrone-world-model/releases/download"


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify only, no downloads")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    with open(LOCK) as f:
        lock = json.load(f)

    if args.selftest:
        # lock integrity: schema + full-length hashes + unique names/dests
        arts = lock["artifacts"]
        assert lock["release"] and arts, "lock must pin a release and artifacts"
        names = [a["name"] for a in arts]
        assert len(set(names)) == len(names), "duplicate asset names"
        by_name = {a["name"]: a for a in arts}
        for a in arts:
            assert set(a) >= {"name", "dest", "sha256", "what"}, f"bad entry {a}"
            assert len(a["sha256"]) == 64, f"{a['name']}: full sha256 required"
            assert not os.path.isabs(a["dest"]), "dests must be repo-relative"
            # a detection head is only valid with the latent it was trained
            # on — its 'wm' field must name another lock entry
            if "wm" in a:
                assert a["wm"] in by_name, f"{a['name']}: wm '{a['wm']}' not in lock"
        print(
            f"FETCH-CHAMPIONS OK: lock pins {len(arts)} artifacts to "
            f"'{lock['release']}', schema + hash-length + head->wm asserts green"
        )
        return

    ok = True
    for a in lock["artifacts"]:
        dest = os.path.join(ROOT, a["dest"])
        if os.path.exists(dest) and _sha256(dest) == a["sha256"]:
            print(f"  [ok  ] {a['dest']} (verified)")
            continue
        if args.check:
            print(f"  [MISS] {a['dest']} — run: python -m scripts.fetch_champions")
            ok = False
            continue
        url = f"{BASE}/{lock['release']}/{a['name']}"
        print(f"  [....] {a['dest']} <- {url}")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        tmp = dest + ".part"
        urllib.request.urlretrieve(url, tmp)  # noqa: S310 — pinned https URL
        got = _sha256(tmp)
        if got != a["sha256"]:
            os.remove(tmp)
            print(f"  [FAIL] {a['name']}: sha256 mismatch (got {got[:16]}…)")
            ok = False
            continue
        os.replace(tmp, dest)
        print(f"  [ok  ] {a['dest']} (downloaded + verified)")
    print(f"FETCH-CHAMPIONS {'OK' if ok else 'FAIL'}")
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
