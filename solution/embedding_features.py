#!/usr/bin/env python3
"""Precompute candidate text embeddings for semantic ranking experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import time
from pathlib import Path
from typing import Any

import numpy as np

from analysis.common import DEFAULT_DATASET, REPO_ROOT
from solution.precompute import iter_candidates_with_hash
from solution.text_features import career_weighted_text


EMBEDDING_VERSION = "candidate-embeddings-minilm-l12-0.1.0"
DEFAULT_MODEL_PATH = Path(
    "/home/nitin/.cache/huggingface/hub/"
    "models--sentence-transformers--all-MiniLM-L12-v2/"
    "snapshots/c004d8e3e901237d8fa7e9fff12774962e391ce5"
)
DEFAULT_ARTIFACT_DIR = REPO_ROOT / "artifacts" / "solution"
DEFAULT_EMBEDDINGS = DEFAULT_ARTIFACT_DIR / "candidate_embeddings_minilm_l12.npy"
DEFAULT_IDS = DEFAULT_ARTIFACT_DIR / "candidate_embedding_ids.json"
DEFAULT_MANIFEST = DEFAULT_ARTIFACT_DIR / "candidate_embeddings_manifest.json"


class TransformerEmbedder:
    """Small mean-pooled transformer embedder with lazy heavy imports."""

    def __init__(
        self,
        model_path: Path,
        max_length: int = 256,
        device: str = "cpu",
    ) -> None:
        from transformers import AutoModel, AutoTokenizer
        import torch

        self.torch = torch
        self.device = device
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            local_files_only=True,
        )
        self.model = AutoModel.from_pretrained(
            model_path,
            local_files_only=True,
        )
        self.model.to(device)
        self.model.eval()

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        with self.torch.no_grad():
            output = self.model(**encoded).last_hidden_state
        mask = encoded["attention_mask"].unsqueeze(-1).float()
        pooled = (output * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        pooled = self.torch.nn.functional.normalize(pooled, p=2, dim=1)
        return pooled.detach().cpu().numpy().astype(np.float32)


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_candidates(candidates_path: Path, limit: int | None = None) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    for _, raw_line in iter_candidates_with_hash(candidates_path):
        digest.update(raw_line)
        count += 1
        if limit and count >= limit:
            break
    return count, digest.hexdigest()


def build_embedding_artifacts(
    candidates_path: Path,
    model_path: Path,
    embeddings_path: Path = DEFAULT_EMBEDDINGS,
    ids_path: Path = DEFAULT_IDS,
    manifest_path: Path = DEFAULT_MANIFEST,
    batch_size: int = 32,
    max_length: int = 256,
    limit: int | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    if not model_path.is_dir():
        raise FileNotFoundError(f"embedding model directory not found: {model_path}")
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    ids_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    candidate_count, candidate_sha = count_candidates(candidates_path, limit)
    embedder = TransformerEmbedder(model_path, max_length=max_length)

    ids: list[str] = []
    batch_ids: list[str] = []
    batch_texts: list[str] = []
    embeddings = None
    written = 0
    dimension = None

    def flush_batch() -> None:
        nonlocal embeddings, written, dimension
        if not batch_texts:
            return
        vectors = embedder.encode(batch_texts)
        if dimension is None:
            dimension = int(vectors.shape[1])
            embeddings = np.lib.format.open_memmap(
                embeddings_path,
                mode="w+",
                dtype=np.float16,
                shape=(candidate_count, dimension),
            )
        if vectors.shape[1] != dimension:
            raise ValueError("embedding dimension changed during precompute")
        assert embeddings is not None
        end = written + len(batch_texts)
        embeddings[written:end] = vectors.astype(np.float16)
        ids.extend(batch_ids)
        written = end
        batch_ids.clear()
        batch_texts.clear()

    for index, (candidate, _) in enumerate(iter_candidates_with_hash(candidates_path), 1):
        batch_ids.append(str(candidate["candidate_id"]))
        batch_texts.append(career_weighted_text(candidate))
        if len(batch_texts) >= batch_size:
            flush_batch()
        if limit and index >= limit:
            break
    flush_batch()
    if embeddings is not None:
        embeddings.flush()
    if written != candidate_count:
        raise ValueError(f"wrote {written} embeddings for {candidate_count} candidates")

    ids_path.write_text(
        json.dumps(ids, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    elapsed = time.perf_counter() - started
    manifest = {
        "embedding_version": EMBEDDING_VERSION,
        "candidate_count": candidate_count,
        "embedding_dimension": dimension,
        "model": {
            "path": str(model_path),
            "config_sha256": sha256_file(model_path / "config.json"),
            "weights_sha256": sha256_file(model_path / "model.safetensors"),
        },
        "inputs": {
            "candidates": {
                "path": str(candidates_path),
                "sha256": candidate_sha,
            }
        },
        "outputs": {
            "embeddings": {
                "path": str(embeddings_path),
                "sha256": sha256_file(embeddings_path),
                "bytes": embeddings_path.stat().st_size,
            },
            "candidate_ids": {
                "path": str(ids_path),
                "sha256": sha256_file(ids_path),
                "bytes": ids_path.stat().st_size,
            },
        },
        "batch_size": batch_size,
        "max_length": max_length,
        "elapsed_seconds": round(elapsed, 3),
        "max_rss_mb": round(peak_rss_mb(), 1),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--ids", type=Path, default=DEFAULT_IDS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_embedding_artifacts(
        repo_path(args.candidates),
        repo_path(args.model),
        repo_path(args.out),
        repo_path(args.ids),
        repo_path(args.manifest),
        args.batch_size,
        args.max_length,
        args.limit,
    )
    print(
        f"Embedded {manifest['candidate_count']:,} candidates "
        f"({manifest['embedding_dimension']} dims) "
        f"in {manifest['elapsed_seconds']:.3f}s; "
        f"maximum memory used {manifest['max_rss_mb']:.1f} MB; "
        f"wrote {manifest['outputs']['embeddings']['path']}"
    )


if __name__ == "__main__":
    main()
