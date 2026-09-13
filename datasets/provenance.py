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
    print("DATASET-PROVENANCE OK: exact file reuse, rename, legacy unknown identity")


if __name__ == "__main__":
    selftest()
