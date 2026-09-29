"""Publish research checkpoints without replacing locked or existing artifacts.

    python -m world_model.checkpoint_io

The lock reserves paths even on artifactless checkouts. Only a caller's
explicit selftest replacement may overwrite an ordinary file. Serialization
finishes in a sibling temporary file; new publication uses a hard link so a
concurrent writer cannot be replaced. No model training occurs here.
"""

import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_destination(path, *, overwrite=False):
    """Validate before expensive work, then again immediately before writing."""
    path = Path(path).absolute()
    lock = json.loads((ROOT / "artifacts.lock.json").read_text())
    protected = [ROOT / entry["dest"] for entry in lock["artifacts"]]
    resolved = path.resolve()
    for reserved in protected:
        if resolved == reserved.resolve() or (
            path.exists() and reserved.exists() and path.samefile(reserved)
        ):
            raise ValueError(
                f"locked artifact destination: {path}; use --out with a new "
                "candidate filename (fetch_champions restores locked artifacts)"
            )
    if path.is_symlink():
        raise ValueError(f"checkpoint destination is a symlink: {path}")
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"checkpoint exists: {path}; choose a new --out")
        if not path.is_file():
            raise ValueError(f"checkpoint destination is not a file: {path}")
    return resolved


def publish_checkpoint(path, writer, *, overwrite=False):
    """Atomically publish bytes supplied by writer(open_binary_file)."""
    destination = check_destination(path, overwrite=overwrite)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            writer(stream.file)
            stream.flush()
            os.fsync(stream.fileno())
        check_destination(destination, overwrite=overwrite)
        if overwrite:
            os.replace(temporary, destination)
        else:
            os.link(temporary, destination)  # atomically fails if another writer won
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination


def save_checkpoint(checkpoint, path, *, overwrite=False):
    """Atomic visibility; failed saves preserve prior files and remove temporaries."""
    import torch

    return publish_checkpoint(
        path, lambda stream: torch.save(checkpoint, stream), overwrite=overwrite
    )


def selftest():
    from unittest.mock import patch

    import torch

    with tempfile.TemporaryDirectory(prefix="checkpoint_io_selftest_") as tmp:
        root = Path(tmp)
        lock = root / "artifacts.lock.json"
        lock.write_text(
            json.dumps(
                {
                    "artifacts": [
                        {"dest": "world_model.pth"},
                        {"dest": "world_model_unified.pth"},
                        {"dest": "policy.zip"},
                    ]
                }
            )
        )
        with patch(__name__ + ".ROOT", root):
            for name in ("world_model.pth", "world_model_unified.pth", "policy.zip"):
                for overwrite in (False, True):
                    try:
                        check_destination(root / name, overwrite=overwrite)
                    except ValueError as exc:
                        assert "locked artifact" in str(exc)
                    else:
                        raise AssertionError("missing locked path accepted")
            champion = root / "world_model.pth"
            champion.write_bytes(b"synthetic champion")
            symlink, hardlink = root / "alias.pth", root / "hardlink.pth"
            symlink.symlink_to(champion)
            os.link(champion, hardlink)
            for alias in (champion, symlink, hardlink):
                try:
                    save_checkpoint({}, alias, overwrite=True)
                except ValueError:
                    pass
                else:
                    raise AssertionError("locked inode overwritten through alias")
            candidate = root / "nested/candidate.pth"
            save_checkpoint({"tensor": torch.arange(3)}, candidate)
            assert torch.equal(
                torch.load(candidate, weights_only=True)["tensor"], torch.arange(3)
            )
            before = candidate.read_bytes()
            try:
                save_checkpoint({}, candidate)
            except FileExistsError:
                pass
            else:
                raise AssertionError("existing research checkpoint overwritten")

            def failed_save(value, stream):
                stream.write(b"partial serialization")
                raise RuntimeError("synthetic serialization failure")

            with patch("torch.save", side_effect=failed_save):
                try:
                    save_checkpoint({}, candidate, overwrite=True)
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("serialization failure swallowed")
            assert candidate.read_bytes() == before
            assert not list(candidate.parent.glob(".*.tmp"))
            save_checkpoint({"replaced_selftest": True}, candidate, overwrite=True)
            assert torch.load(candidate, weights_only=True)["replaced_selftest"]
            contender = root / "contender.pth"
            original_link = os.link

            def competing_link(source, dest):
                Path(dest).write_bytes(b"winner")
                return original_link(source, dest)

            with patch("os.link", side_effect=competing_link):
                try:
                    save_checkpoint({}, contender)
                except FileExistsError:
                    pass
                else:
                    raise AssertionError("concurrent publication replaced")
            assert contender.read_bytes() == b"winner"
            assert not list(root.glob(".*.tmp"))
            assert champion.read_bytes() == b"synthetic champion"
    print("CHECKPOINT-IO OK: locked paths/aliases, no overwrite, atomic failure/race")


if __name__ == "__main__":
    selftest()
