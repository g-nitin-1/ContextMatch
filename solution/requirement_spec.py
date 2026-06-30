#!/usr/bin/env python3
"""Requirement-spec schema and loader for the general ranker."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SPEC_VERSION = "requirement-spec-0.1.0"
DEFAULT_SPEC = Path(__file__).with_name("specs") / "senior_ai_engineer.json"
SENIORITY_LEVELS = {"unspecified", "junior", "mid", "senior", "staff", "principal"}
SENIORITY_TRACKS = {"either", "ic", "management"}


@dataclass(frozen=True)
class RequirementItem:
    id: str
    desc: str
    weight: float
    evidence_signals: tuple[str, ...]
    compound: str | None = None
    compounds: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any], section: str) -> "RequirementItem":
        required = ("id", "desc", "weight", "evidence_signals")
        for key in required:
            if key not in payload:
                raise ValueError(f"{section} item missing {key}")
        item_id = str(payload["id"]).strip()
        desc = str(payload["desc"]).strip()
        try:
            weight = float(payload["weight"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{section}.{item_id} has invalid weight") from exc
        signals = tuple(str(value).strip() for value in payload["evidence_signals"])
        if not item_id or not desc:
            raise ValueError(f"{section} item id/desc must be non-empty")
        if weight <= 0:
            raise ValueError(f"{section}.{item_id} weight must be positive")
        if not signals or any(not signal for signal in signals):
            raise ValueError(f"{section}.{item_id} evidence_signals must be non-empty")
        compounds = _compound_ids(payload)
        return cls(
            id=item_id,
            desc=desc,
            weight=weight,
            evidence_signals=signals,
            compound=compounds[0] if compounds else None,
            compounds=compounds,
        )


@dataclass(frozen=True)
class RequirementSpec:
    schema_version: str
    role_title: str
    seniority: dict[str, Any]
    must_have: tuple[RequirementItem, ...]
    nice_to_have: tuple[RequirementItem, ...]
    hard_disqualifiers: tuple[str, ...]
    soft_negatives: tuple[str, ...]
    location: dict[str, Any]
    semantic_queries: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RequirementSpec":
        if payload.get("schema_version") != SPEC_VERSION:
            raise ValueError(
                "unsupported requirement spec version: "
                f"{payload.get('schema_version')!r}"
            )
        role_title = str(payload.get("role_title", "")).strip()
        if not role_title:
            raise ValueError("requirement spec missing role_title")
        seniority = normalize_seniority(payload.get("seniority"))
        if not isinstance(seniority, dict):
            raise ValueError("requirement spec seniority must be an object")
        must_have = tuple(
            RequirementItem.from_dict(item, "must_have")
            for item in payload.get("must_have", [])
        )
        nice_to_have = tuple(
            RequirementItem.from_dict(item, "nice_to_have")
            for item in payload.get("nice_to_have", [])
        )
        if not must_have:
            raise ValueError("requirement spec must_have must be non-empty")
        hard_disqualifiers = _rule_ids(payload.get("hard_disqualifiers", []))
        soft_negatives = _rule_ids(payload.get("soft_negatives", []))
        location = payload.get("location", {})
        if not isinstance(location, dict):
            raise ValueError("requirement spec location must be an object")
        semantic_queries = tuple(
            str(query).strip() for query in payload.get("semantic_queries", [])
        )
        if not semantic_queries or any(not query for query in semantic_queries):
            raise ValueError("requirement spec semantic_queries must be non-empty")
        return cls(
            schema_version=SPEC_VERSION,
            role_title=role_title,
            seniority=seniority,
            must_have=must_have,
            nice_to_have=nice_to_have,
            hard_disqualifiers=hard_disqualifiers,
            soft_negatives=soft_negatives,
            location=location,
            semantic_queries=semantic_queries,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["must_have"] = [asdict(item) for item in self.must_have]
        payload["nice_to_have"] = [asdict(item) for item in self.nice_to_have]
        payload["hard_disqualifiers"] = [
            {"id": rule_id, "scope": "candidate_rule"}
            for rule_id in self.hard_disqualifiers
        ]
        payload["soft_negatives"] = [
            {"id": rule_id, "scope": "candidate_rule"}
            for rule_id in self.soft_negatives
        ]
        return payload

    @property
    def evidence_signal_ids(self) -> set[str]:
        signals: set[str] = set()
        for item in self.must_have + self.nice_to_have:
            signals.update(item.evidence_signals)
        return signals

    @property
    def compound_ids(self) -> set[str]:
        compounds: set[str] = set()
        for item in self.must_have + self.nice_to_have:
            compounds.update(item.compounds)
        return compounds


def _rule_ids(values: Any) -> tuple[str, ...]:
    if not isinstance(values, list):
        raise ValueError("rule list must be a list")
    rule_ids = []
    for value in values:
        if isinstance(value, dict):
            rule_id = str(value.get("id", "")).strip()
        else:
            rule_id = str(value).strip()
        if not rule_id:
            raise ValueError("rule id must be non-empty")
        rule_ids.append(rule_id)
    return tuple(rule_ids)


def _compound_ids(payload: dict[str, Any]) -> tuple[str, ...]:
    values: list[Any] = []
    if payload.get("compound"):
        values.append(payload["compound"])
    if "compounds" in payload:
        compounds = payload["compounds"]
        if not isinstance(compounds, list):
            raise ValueError("compounds must be a list")
        values.extend(compounds)

    normalized = []
    seen = set()
    for value in values:
        compound_id = str(value).strip()
        if not compound_id:
            raise ValueError("compound id must be non-empty")
        if compound_id not in seen:
            seen.add(compound_id)
            normalized.append(compound_id)
    return tuple(normalized)


def normalize_seniority(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("requirement spec seniority must be an object")
    level = str(payload.get("level", "unspecified")).strip().lower()
    track = str(payload.get("track", "either")).strip().lower()
    if level not in SENIORITY_LEVELS:
        raise ValueError(f"unsupported seniority level: {level!r}")
    if track not in SENIORITY_TRACKS:
        raise ValueError(f"unsupported seniority track: {track!r}")
    try:
        strength = float(payload.get("strength", 0.0))
    except (TypeError, ValueError) as exc:
        raise ValueError("seniority strength must be numeric") from exc
    strength = max(0.0, min(0.75, strength))
    return {
        **payload,
        "level": level,
        "track": track,
        "min_years": payload.get("min_years"),
        "max_years": payload.get("max_years"),
        "hard": bool(payload.get("hard", False)),
        "strength": strength,
    }


def load_spec(path: Path = DEFAULT_SPEC) -> RequirementSpec:
    return RequirementSpec.from_dict(json.loads(path.read_text(encoding="utf-8")))


def write_spec(spec: RequirementSpec, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(spec.to_dict(), indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--write-copy", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec = load_spec(args.spec)
    if args.write_copy:
        write_spec(spec, args.write_copy)
        print(f"Wrote {args.write_copy}")
    else:
        print(json.dumps(spec.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
