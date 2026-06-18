import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rank import load_freeze_manifest, resolve_runtime_assets


class RankEntrypointTests(unittest.TestCase):
    def test_freeze_manifest_must_be_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "freeze.json"
            path.write_text(
                json.dumps(
                    {
                        "status": "draft",
                        "scorer_version": "0.2.0",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "frozen_pre_teacher"):
                load_freeze_manifest(path)

    def test_runtime_asset_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            assets = {}
            for asset_id in (
                "generator_manifest",
                "jd_evidence_catalog",
                "knowledge_base",
            ):
                path = root / f"{asset_id}.json"
                path.write_text("{}", encoding="utf-8")
                assets[asset_id] = {
                    "path": path.name,
                    "sha256": "not-the-real-hash",
                }

            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                resolve_runtime_assets({"assets": assets}, root)


if __name__ == "__main__":
    unittest.main()
