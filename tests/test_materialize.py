"""Tests for the neutral-format → per-host skill materialiser.

The same ``.skill.md`` source must be materialised into both
``.claude/skills/<name>/SKILL.md`` and
``.cursor/skills/<name>/SKILL.md`` with byte-identical content (the
format itself IS the SKILL.md format the existing
agent-readiness-skill uses).
"""
from __future__ import annotations

from pathlib import Path

from materialize import materialize_directory, materialize_skill


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"


def test_materialize_skill_writes_both_host_layouts(tmp_path: Path) -> None:
    src = SKILLS_DIR / "manifest" / "validate.skill.md"
    assert src.exists(), "test fixture missing"

    materialize_skill(src, out_root=tmp_path, name="manifest-validate")

    claude = tmp_path / ".claude" / "skills" / "manifest-validate" / "SKILL.md"
    cursor = tmp_path / ".cursor" / "skills" / "manifest-validate" / "SKILL.md"
    assert claude.exists()
    assert cursor.exists()
    assert claude.read_bytes() == cursor.read_bytes()
    assert claude.read_bytes() == src.read_bytes()


def test_materialize_directory_finds_all_skill_md_files(tmp_path: Path) -> None:
    n = materialize_directory(SKILLS_DIR, out_root=tmp_path)
    # M1 has exactly one .skill.md source so far.
    assert n == 1
    claude_skills = sorted((tmp_path / ".claude" / "skills").iterdir())
    assert len(claude_skills) == 1
    assert claude_skills[0].name == "manifest-validate"


def test_materialize_skill_overwrites_existing(tmp_path: Path) -> None:
    src = SKILLS_DIR / "manifest" / "validate.skill.md"
    out_skill = tmp_path / ".claude" / "skills" / "manifest-validate" / "SKILL.md"
    out_skill.parent.mkdir(parents=True)
    out_skill.write_text("stale content")
    materialize_skill(src, out_root=tmp_path, name="manifest-validate")
    assert "stale content" not in out_skill.read_text()


def test_materialize_skill_naming_convention(tmp_path: Path) -> None:
    src = SKILLS_DIR / "manifest" / "validate.skill.md"
    materialize_skill(src, out_root=tmp_path)
    assert (tmp_path / ".claude" / "skills" / "manifest-validate").is_dir()
    assert (tmp_path / ".cursor" / "skills" / "manifest-validate").is_dir()
