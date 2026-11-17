"""
CircuitSnap — Modular agentskills.io Progressive-Disclosure Skill Loader
Discovers, parses, and dynamically injects domain-specific engineering skills
into the reasoning engine prompt with zero heavy dependencies.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)

DEFAULT_SKILLS_DIR = Path(__file__).resolve().parent / "skills"


@dataclass
class SkillMetadata:
    """Lightweight metadata descriptor loaded at index time (content deferred)."""
    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    workflow: Optional[str] = None
    file_path: Optional[Path] = None


@dataclass
class SkillMatch:
    """Disclosed skill match with progressive content payload."""
    name: str
    description: str
    content: str
    score: float
    triggers: list[str] = field(default_factory=list)
    workflow: Optional[str] = None


_SKILLS_CATALOG: dict[str, SkillMetadata] = {}


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """
    Parses YAML frontmatter enclosed by '---' lines using stdlib re.
    Returns (metadata_dict, body_markdown).
    """
    match = FRONTMATTER_PATTERN.match(text.strip())
    if not match:
        return {}, text

    yaml_block = match.group(1)
    body = match.group(2).strip()

    meta: dict[str, Any] = {}
    current_list_key = None

    for raw_line in yaml_block.splitlines():
        line = raw_line.rstrip()
        if not line or line.startswith("#"):
            continue

        list_match = re.match(r"^\s*-\s+(.*)$", line)
        if list_match and current_list_key:
            val = list_match.group(1).strip().strip("'\"")
            meta.setdefault(current_list_key, []).append(val)
            continue

        kv_match = re.match(r"^([a-zA-Z0-9_-]+)\s*:\s*(.*)$", line)
        if kv_match:
            key = kv_match.group(1).strip()
            val = kv_match.group(2).strip()
            if not val:
                current_list_key = key
                meta[key] = []
            elif val.startswith("[") and val.endswith("]"):
                current_list_key = None
                items = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
                meta[key] = items
            else:
                current_list_key = None
                meta[key] = val.strip("'\"")

    return meta, body


def load_skill_catalog(skills_dir: Path | None = None, force_refresh: bool = False) -> dict[str, SkillMetadata]:
    """
    Scans backend/skills/*/SKILL.md, validates agentskills.io constraints,
    and caches SkillMetadata descriptors in memory.
    Markdown bodies are deferred until query match time (progressive disclosure).
    """
    global _SKILLS_CATALOG
    if _SKILLS_CATALOG and not force_refresh:
        return _SKILLS_CATALOG

    target_dir = Path(skills_dir) if skills_dir else DEFAULT_SKILLS_DIR
    catalog: dict[str, SkillMetadata] = {}

    if not target_dir.exists() or not target_dir.is_dir():
        logger.debug("Skills directory %s does not exist", target_dir)
        _SKILLS_CATALOG = catalog
        return catalog

    for skill_file in target_dir.glob("*/SKILL.md"):
        parent_dir_name = skill_file.parent.name
        try:
            content = skill_file.read_text(encoding="utf-8")
            meta, _ = parse_frontmatter(content)
            name = str(meta.get("name", "")).strip()

            if not name:
                logger.warning("Skill %s missing 'name' in frontmatter", skill_file)
                continue

            if not SKILL_NAME_PATTERN.match(name):
                logger.warning("Skill name '%s' violates agentskills.io slug pattern", name)
                continue

            if name != parent_dir_name:
                logger.warning(
                    "Skill name '%s' does not match parent directory '%s'",
                    name, parent_dir_name
                )
                continue

            description = str(meta.get("description", "")).strip()
            triggers = [str(t).strip().lower() for t in meta.get("triggers", []) if str(t).strip()]
            workflow = meta.get("workflow")
            if workflow:
                workflow = str(workflow).strip()

            catalog[name] = SkillMetadata(
                name=name,
                description=description,
                triggers=triggers,
                workflow=workflow,
                file_path=skill_file,
            )
        except Exception as err:
            logger.warning("Failed parsing skill file %s: %s", skill_file, err)

    _SKILLS_CATALOG = catalog
    logger.info("Loaded %d engineering skills into catalog", len(catalog))
    return catalog


def match_skills(
    query: str,
    workflow: str = "general_electronics",
    max_skills: int = 2,
    skills_dir: Path | None = None,
) -> list[SkillMatch]:
    """
    Scores frontmatter metadata against user query and workflow.
    Loads and discloses full SKILL.md body only for winning matches.
    """
    catalog = load_skill_catalog(skills_dir=skills_dir)
    if not catalog or not query:
        return []

    q_lower = query.lower()
    q_tokens = set(re.findall(r"\b[a-z0-9-]+\b", q_lower))

    stop_words = {
        "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of",
        "with", "is", "are", "what", "how", "find", "solve", "calculate", "tell", "me"
    }
    meaningful_q_tokens = q_tokens - stop_words

    candidates: list[tuple[float, SkillMetadata]] = []

    for skill in catalog.values():
        score = 0.0

        # Exact skill name mentioned
        skill_name_phrase = skill.name.replace("-", " ")
        if skill.name in q_lower or skill_name_phrase in q_lower:
            score += 6.0

        # Triggers evaluation
        for trig in skill.triggers:
            if trig in q_lower:
                score += 4.5
            else:
                trig_tokens = set(re.findall(r"\b[a-z0-9-]+\b", trig)) - stop_words
                if trig_tokens and trig_tokens.issubset(meaningful_q_tokens):
                    score += 3.0

        # Description token overlap
        desc_tokens = set(re.findall(r"\b[a-z0-9-]+\b", skill.description.lower())) - stop_words
        overlap = desc_tokens.intersection(meaningful_q_tokens)
        score += len(overlap) * 1.0

        # Workflow alignment boost
        if skill.workflow and skill.workflow == workflow:
            score += 1.5

        if score >= 3.0:
            candidates.append((score, skill))

    # Sort descending by score
    candidates.sort(key=lambda x: x[0], reverse=True)
    selected = candidates[:max_skills]

    matches: list[SkillMatch] = []
    for score, meta in selected:
        content_body = ""
        if meta.file_path and meta.file_path.exists():
            try:
                raw_text = meta.file_path.read_text(encoding="utf-8")
                _, content_body = parse_frontmatter(raw_text)
            except Exception as err:
                logger.warning("Failed progressive disclosure for %s: %s", meta.name, err)

        matches.append(
            SkillMatch(
                name=meta.name,
                description=meta.description,
                content=content_body,
                score=round(score, 2),
                triggers=meta.triggers,
                workflow=meta.workflow,
            )
        )

    return matches


def list_loaded_skills() -> list[dict[str, Any]]:
    """Returns metadata for all indexed skills."""
    catalog = load_skill_catalog()
    return [
        {
            "name": s.name,
            "description": s.description,
            "triggers": s.triggers,
            "workflow": s.workflow,
            "path": str(s.file_path) if s.file_path else "",
        }
        for s in catalog.values()
    ]
