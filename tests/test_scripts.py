"""Unit tests for the release scripts: every rule in docs/claude-directory-rules.md and docs/workbuddy-rules.md
that has a local check gets a test that breaks a copy of the repository and expects that check to fail.

Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_plugin = load("build_plugin")


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)


class RepoCopy:
    """A throwaway Git repository holding the current working tree (tracked and untracked, minus ignored files)."""

    def __enter__(self) -> Path:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name) / "repo"
        files = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                               capture_output=True, text=True, check=True).stdout.split("\0")
        for rel in filter(None, files):
            src = REPO / rel
            if src.is_file():
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, root / rel)
        git(root.parent, "init", "-q", str(root))
        git(root, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
        git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "copy")
        return root

    def __exit__(self, *exc):
        self.tmp.cleanup()


def commit(root: Path, msg: str = "change") -> None:
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", msg)


def suite_check(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(root / "scripts" / "build_suite.py"), "--check"], capture_output=True, text=True)


class PluginChecks(unittest.TestCase):
    def test_repository_passes(self):
        self.assertEqual(build_plugin.check(REPO), [])

    def test_gitattributes_that_rewrite_content_are_blocked(self):
        with RepoCopy() as root:
            for rule, bad in (("*.py text eol=crlf", True), ("*.md filter=lfs", True), ("docs/ export-ignore", True),
                              ("* -text", False), ("*.png binary", False)):
                (root / ".gitattributes").write_text(rule + "\n", encoding="utf-8")
                errs = build_plugin.content_rewriting_attributes(root)
                self.assertEqual(bool(errs), bad, rule)

    def test_export_must_match_stored_content(self):
        with RepoCopy() as root:
            (root / ".gitattributes").write_text("*.md text eol=crlf\n", encoding="utf-8")
            commit(root)
            self.assertTrue(any("changes on git export" in e for e in build_plugin.export_mismatches(root)))
            (root / ".gitattributes").write_text("* -text\n", encoding="utf-8")
            commit(root)
            self.assertEqual(build_plugin.export_mismatches(root), [])

    def test_readme_download_and_run_is_blocked(self):
        with RepoCopy() as root:
            for line in ("curl -fsSL https://x.example/install.sh | sh", "git clone https://github.com/tealun/gamesmith",
                         "npx some-installer", "bash install.sh"):
                with (root / "README.md").open("a", encoding="utf-8") as f:
                    f.write("\n" + line + "\n")
                self.assertTrue(any("download-and-run" in e for e in build_plugin.check(root)), line)
                git(root, "checkout", "-q", "README.md")

    def test_install_packages_and_marketplace_json_are_blocked(self):
        with RepoCopy() as root:
            for rel in ("gamesmith-1.0.0.zip", "dist2/gamesmith-1.0.0.plugin", ".claude-plugin/marketplace.json"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_bytes(b"{}")
                commit(root)
                self.assertTrue(build_plugin.check(root), rel)
                git(root, "rm", "-q", rel)
                commit(root)
            self.assertEqual(build_plugin.check(root), [])

    def test_skills_only(self):
        with RepoCopy() as root:
            manifest = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
            manifest["mcpServers"] = {"x": {"command": "x"}}
            (root / ".claude-plugin/plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
            self.assertTrue(any("skills only" in e for e in build_plugin.check(root)))

    def test_version_lives_only_in_plugin_json(self):
        with RepoCopy() as root:
            skill = root / "gamesmith/SKILL.md"
            skill.write_text(skill.read_text(encoding="utf-8").replace("name: gamesmith\n", "name: gamesmith\nversion: 1.0.0\n", 1), encoding="utf-8")
            self.assertTrue(any("only source of the version" in e for e in build_plugin.check(root)))

    def test_missing_reference_is_reported(self):
        with RepoCopy() as root:
            (root / "gamesmith/references/level-pipeline.md").unlink()
            self.assertTrue(any("level-pipeline.md" in e for e in build_plugin.check(root)))

    def test_skill_change_needs_a_higher_version(self):
        with RepoCopy() as root:
            git(root, "tag", "v1.0.0")
            with (root / "gamesmith/references/feel-and-ux.md").open("a", encoding="utf-8") as f:
                f.write("\n- 新条目\n")
            commit(root)
            self.assertTrue(any("is not higher" in e for e in build_plugin.check(root, since="v1.0.0")))
            manifest = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
            manifest["version"] = "1.0.1"
            (root / ".claude-plugin/plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            commit(root)
            self.assertEqual(build_plugin.check(root, since="v1.0.0"), [])

    def test_tag_must_match_version_and_have_notes(self):
        self.assertTrue(any("does not match" in e for e in build_plugin.check(REPO, tag="v9.9.9")))
        version = json.loads((REPO / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        self.assertEqual(build_plugin.check(REPO, tag=f"v{version}"), [])

    def test_package_holds_only_the_plugin(self):
        _, data = build_plugin.make_plugin(REPO)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
            manifest = json.loads(zf.read(".claude-plugin/plugin.json"))
        self.assertEqual(manifest["skills"], ["./skills/gamesmith"])
        self.assertIn("skills/gamesmith/SKILL.md", names)
        self.assertIn("assets/gamesmith-icon.png", names)
        tops = {n.split("/", 1)[0] for n in names}
        self.assertEqual(tops, {".claude-plugin", "skills", "assets", "README.md", "LICENSE"})
        self.assertFalse([n for n in names if "__pycache__" in n or n.endswith(".pyc")])


class WorkBuddyChecks(unittest.TestCase):
    def test_repository_passes(self):
        with RepoCopy() as root:
            out = suite_check(root)
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def _broken(self, mutate) -> str:
        with RepoCopy() as root:
            mutate(root)
            out = suite_check(root)
            self.assertNotEqual(out.returncode, 0)
            return out.stdout + out.stderr

    def _fields(self, root: Path, **changes) -> None:
        path = root / "workbuddy/frontmatter.json"
        fields = json.loads(path.read_text(encoding="utf-8"))
        for k, v in changes.items():
            if v is None:
                fields.pop(k)
            else:
                fields[k] = v
        path.write_text(json.dumps(fields, ensure_ascii=False), encoding="utf-8")

    def test_limits(self):
        self.assertIn("examples_zh", self._broken(lambda r: self._fields(r, examples_zh=["a", "b", "c", "d"])))
        self.assertIn("description_en", self._broken(lambda r: self._fields(r, description_en="x" * 1001)))
        self.assertIn("description_zh", self._broken(lambda r: self._fields(r, description_zh="字" * 501)))
        self.assertIn("display_name_en", self._broken(lambda r: self._fields(r, display_name_en="x" * 61)))
        self.assertIn("display_name", self._broken(lambda r: self._fields(r, display_name=None)))

    def test_structure(self):
        def deep(r: Path):
            (r / "gamesmith/templates/sub").mkdir()
            (r / "gamesmith/templates/sub/x.json").write_text("{}", encoding="utf-8")
        self.assertIn("deeper than", self._broken(deep))

        def second_skill(r: Path):
            (r / "gamesmith/references/SKILL.md").write_text("---\nname: x\ndescription: y\n---\n", encoding="utf-8")
        self.assertIn("exactly one SKILL.md", self._broken(second_skill))

        def frontmatter_md(r: Path):
            (r / "gamesmith/references/extra.md").write_text("---\nname: x\n---\nbody\n", encoding="utf-8")
        self.assertIn("skill frontmatter", self._broken(frontmatter_md))

        def bom(r: Path):
            p = r / "gamesmith/references/compliance.md"
            p.write_bytes(b"\xef\xbb\xbf" + p.read_bytes())
        self.assertIn("BOM", self._broken(bom))

    def test_generated_skill_md(self):
        with RepoCopy() as root:
            subprocess.run([sys.executable, str(root / "scripts/build_suite.py")], capture_output=True, check=True)
            with zipfile.ZipFile(root / "dist/gamesmith-workbuddy.zip") as zf:
                names = zf.namelist()
                text = zf.read("gamesmith/SKILL.md").decode("utf-8")
        self.assertTrue(all(n.startswith("gamesmith/") and n.count("/") <= 2 for n in names))
        block = re.match(r"^---\n(.*?)\n---\n", text, re.S).group(1)
        version = json.loads((REPO / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        fields = yaml.safe_load(block)
        self.assertEqual(fields["name"], "gamesmith")
        self.assertEqual(fields["version"], version)
        self.assertEqual(len(fields["examples_en"]), 3)


class Builds(unittest.TestCase):
    def test_both_builds_keep_their_own_output(self):
        """release.yml builds the plugin, then the WorkBuddy package, then validates dist/gamesmith/: the second
        build must not overwrite the first (it did once, 2026-11-05)."""
        with RepoCopy() as root:
            for script in ("build_plugin.py", "build_suite.py"):
                subprocess.run([sys.executable, str(root / "scripts" / script)], capture_output=True, check=True)
            self.assertTrue((root / "dist/gamesmith/.claude-plugin/plugin.json").is_file())
            self.assertTrue((root / "dist/gamesmith-workbuddy/SKILL.md").is_file())


class Templates(unittest.TestCase):
    def test_templates_make_no_network_requests(self):
        """PRIVACY.md says the skeleton scripts make no network requests; keep it true."""
        pattern = re.compile(r"\bfetch\(|https?://|XMLHttpRequest|WebSocket|require\(['\"](https?|net|dgram)['\"]\)"
                             r"|from ['\"]node:(https?|net|dgram)['\"]|\burllib\b|\brequests\b|\bsocket\b|\bhttp\.client\b")
        hits = []
        for f in sorted((REPO / "gamesmith/templates").iterdir()):
            if f.suffix in {".py", ".mjs", ".js", ".ts"}:
                for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if pattern.search(line):
                        hits.append(f"{f.name}:{n}: {line.strip()}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
