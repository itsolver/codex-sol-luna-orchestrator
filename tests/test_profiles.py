import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXECUTION_ROLES = ("explorer", "worker", "tester", "researcher")


def load_toml(path: Path):
    return tomllib.loads(path.read_text(encoding="utf-8"))


class ProfileTests(unittest.TestCase):
    def test_pro_routes_quality_roles_to_sol(self):
        profile = ROOT / "profiles" / "pro"
        config = load_toml(profile / "codex" / "config.toml")
        self.assertEqual(config["model"], "gpt-5.6-sol")
        self.assertEqual(config["model_reasoning_effort"], "medium")
        self.assertEqual(config["agents"]["default_subagent_model"], "gpt-5.6-luna")
        self.assertEqual(config["agents"]["default_subagent_reasoning_effort"], "max")

        reviewer = load_toml(profile / "codex" / "agents" / "reviewer.toml")
        self.assertEqual(reviewer["model"], "gpt-5.6-sol")
        self.assertEqual(reviewer["model_reasoning_effort"], "low")

        for role in EXECUTION_ROLES:
            with self.subTest(role=role):
                agent = load_toml(profile / "codex" / "agents" / f"{role}.toml")
                self.assertEqual(agent["model"], "gpt-5.6-luna")
                self.assertEqual(agent["model_reasoning_effort"], "max")

    def test_plus_keeps_luna_root_and_uses_sol_reviewer(self):
        profile = ROOT / "profiles" / "plus"
        config = load_toml(profile / "codex" / "config.toml")
        self.assertEqual(config["model"], "gpt-5.6-luna")
        self.assertEqual(config["model_reasoning_effort"], "max")
        self.assertEqual(config["agents"]["default_subagent_model"], "gpt-5.6-luna")
        self.assertEqual(config["agents"]["default_subagent_reasoning_effort"], "medium")

        reviewer = load_toml(profile / "codex" / "agents" / "reviewer.toml")
        self.assertEqual(reviewer["model"], "gpt-5.6-sol")
        self.assertEqual(reviewer["model_reasoning_effort"], "low")

        for role in EXECUTION_ROLES:
            with self.subTest(role=role):
                agent = load_toml(profile / "codex" / "agents" / f"{role}.toml")
                self.assertEqual(agent["model"], "gpt-5.6-luna")
                self.assertEqual(agent["model_reasoning_effort"], "medium")

    def test_profiles_install_only_the_sol_skill(self):
        for plan in ("pro", "plus"):
            with self.subTest(plan=plan):
                skills = ROOT / "profiles" / plan / "agents" / "skills"
                self.assertEqual([path.name for path in skills.iterdir()], ["sol-orchestrator"])
                skill = (skills / "sol-orchestrator" / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("\nname: sol-orchestrator\n", skill)
                self.assertNotIn("gpt-6-astra", skill)

    def test_active_configuration_has_no_astra_model_slug(self):
        paths = [ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "setup.sh", ROOT / "setup.ps1"]
        paths.extend((ROOT / "profiles").rglob("*"))
        paths.extend(path for path in (ROOT / "guides").glob("*.md") if path.name != "token-usage.md")
        for path in paths:
            if path.is_file():
                with self.subTest(path=path.relative_to(ROOT)):
                    self.assertNotIn("gpt-6-astra", path.read_text(encoding="utf-8"))


class ShellInstallerTests(unittest.TestCase):
    def test_installs_each_profile_with_sol_skill(self):
        for plan, choice, root_model in (
            ("pro", "1", "gpt-5.6-sol"),
            ("plus", "2", "gpt-5.6-luna"),
        ):
            with self.subTest(plan=plan), tempfile.TemporaryDirectory() as directory:
                result = subprocess.run(
                    ["sh", str(ROOT / "setup.sh")],
                    input=f"{directory}\n{choice}\n\n\n\n",
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                config = load_toml(Path(directory) / ".codex" / "config.toml")
                self.assertEqual(config["model"], root_model)
                self.assertTrue(
                    (Path(directory) / ".agents" / "skills" / "sol-orchestrator" / "SKILL.md").is_file()
                )
                self.assertFalse((Path(directory) / ".agents" / "skills" / "astra-orchestrator").exists())
                self.assertIn(
                    "`sol-orchestrator` skill",
                    (Path(directory) / "AGENTS.md").read_text(encoding="utf-8"),
                )

    def test_warns_when_a_legacy_astra_skill_remains(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy_skill = Path(directory) / ".agents" / "skills" / "astra-orchestrator"
            legacy_skill.mkdir(parents=True)
            result = subprocess.run(
                ["sh", str(ROOT / "setup.sh")],
                input=f"{directory}\n1\nn\nn\nn\n",
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Sol skill is not installed", result.stderr)
            self.assertIn("Keep it", result.stderr)
            self.assertNotIn("then remove it", result.stderr)
            self.assertTrue(legacy_skill.is_dir())

    def test_upgrades_legacy_agents_directive_without_duplicating_instructions(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            legacy_skill = target / ".agents" / "skills" / "astra-orchestrator"
            legacy_skill.mkdir(parents=True)
            (legacy_skill / "SKILL.md").write_text("legacy\n", encoding="utf-8")
            current_agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
            legacy_agents = current_agents.replace("sol-orchestrator", "astra-orchestrator")
            (target / "AGENTS.md").write_text(legacy_agents, encoding="utf-8")

            result = subprocess.run(
                ["sh", str(ROOT / "setup.sh")],
                input=f"{directory}\n1\nn\n\ny\n\n",
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed_agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(installed_agents, current_agents)
            self.assertNotIn("astra-orchestrator", installed_agents)
            self.assertIn("replaced the legacy astra-orchestrator directive", result.stdout)
            self.assertTrue((target / ".agents" / "skills" / "sol-orchestrator").is_dir())
            self.assertIn("then remove it to avoid loading both skills", result.stderr)

    def test_warns_when_legacy_agents_directive_update_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            legacy_agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8").replace(
                "sol-orchestrator", "astra-orchestrator"
            )
            (target / "AGENTS.md").write_text(legacy_agents, encoding="utf-8")
            result = subprocess.run(
                ["sh", str(ROOT / "setup.sh")],
                input=f"{directory}\n1\nn\nn\nn\n",
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("AGENTS.md still references astra-orchestrator", result.stderr)
            self.assertIn("rerun setup and install AGENTS.md", result.stderr)


if __name__ == "__main__":
    unittest.main()
