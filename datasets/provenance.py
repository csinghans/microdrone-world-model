"""File identity checks, not proof of rollout-level dataset independence.

python -m datasets.provenance
"""

import hashlib
from pathlib import Path


def file_identity(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(chunk)
    return {"path": str(Path(path).resolve()), "sha256": hasher.hexdigest()}


def reject_training_file(training_sha256, evaluation_sha256):
    """Reject known exact file reuse; missing/different hashes prove nothing.

    Repacked/subset/mixed corpora can overlap despite different file hashes.
    Legacy checkpoints may have no recorded identity. Their caller still
    owns the independent-generation assertion.
    """
    if (
        training_sha256
        and evaluation_sha256
        and training_sha256.lower() == evaluation_sha256.lower()
    ):
        raise ValueError(
            "independent holdout reuses the checkpoint's training dataset "
            "(identical SHA-256); use a separately generated exam, or omit "
            "--independent-holdout for the original training-validation split"
        )


def require_training_file(training_sha256, evaluation_sha256):
    """Reject a known different corpus in original training-validation mode.

    Return whether both file hashes were supplied and matched. Missing hashes
    remain compatible with legacy checkpoints/in-memory callers, but cannot
    verify that reconstructing a split from its seed selects the original
    validation rollouts. Recompression or reordering changes file identity.
    """
    if not training_sha256 or not evaluation_sha256:
        return False
    if training_sha256.lower() != evaluation_sha256.lower():
        raise ValueError(
            "training-validation dataset differs from the checkpoint's training "
            "file (SHA-256 mismatch); restore the original corpus to reconstruct "
            "its validation split. --independent-holdout is only for separately "
            "generated exams, not repacked or reordered training data"
        )
    return True


def selftest():
    import tempfile

    with tempfile.TemporaryDirectory(prefix="dataset_identity_selftest_") as tmp:
        a, b = Path(tmp) / "a.npz", Path(tmp) / "renamed.npz"
        a.write_bytes(b"same training corpus")
        b.write_bytes(a.read_bytes())
        ai, bi = file_identity(a), file_identity(b)
        assert ai["path"] != bi["path"] and ai["sha256"] == bi["sha256"]
        for other in (bi["sha256"], bi["sha256"].upper()):
            try:
                reject_training_file(ai["sha256"], other)
            except ValueError:
                pass
            else:
                raise AssertionError("renaming training data bypassed the check")
        b.write_bytes(b"different bytes, not necessarily independent courses")
        reject_training_file(ai["sha256"], file_identity(b)["sha256"])
        reject_training_file(None, ai["sha256"])
        reject_training_file(ai["sha256"], None)
        assert require_training_file(ai["sha256"], bi["sha256"])
        assert require_training_file(ai["sha256"], bi["sha256"].upper())
        assert not require_training_file(None, ai["sha256"])
        assert not require_training_file(ai["sha256"], None)
        try:
            require_training_file(ai["sha256"], file_identity(b)["sha256"])
        except ValueError as exc:
            assert "SHA-256 mismatch" in str(exc)
        else:
            raise AssertionError("wrong training-validation file accepted")
    print(
        "DATASET-PROVENANCE OK: holdout reuse / validation mismatch, "
        "rename, legacy unknown identity"
    )


if __name__ == "__main__":
    selftest()
