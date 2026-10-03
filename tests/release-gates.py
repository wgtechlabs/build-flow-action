"""Exercise the real package evidence script and release job conditions."""

import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {
    name: (ROOT / ".github/workflows" / name).read_text()
    for name in ("app.yml", "package.yml")
}
BASE = {
    "inputs.enable-package": True,
    "inputs.enable-container": True,
    "inputs.enable-codeql": True,
    "inputs.release-dry-run": False,
    "inputs.release-create": True,
    "inputs.release-tag-only": False,
    "inputs.package-publish-enabled": True,
    "inputs.container-push-enabled": True,
    "needs.context.outputs.allow-artifact-publish": "true",
    "needs.context.outputs.allow-package-publish": "true",
    "needs.context.outputs.allow-release-finalize": "true",
    "needs.context.outputs.is-main": "true",
    "needs.ci-gate.result": "success",
    "needs.ci-gate.outputs.resolved-codeql-languages": "javascript-typescript",
    "needs.codeql.result": "success",
    "needs.source-finalize.result": "success",
    "needs.version-plan.result": "success",
    "needs.version-plan.outputs.planned-version-bump-type": "patch",
    "needs.package.result": "success",
    "needs.package.outputs.artifact-published": "true",
    "needs.package.outputs.all-selected-registries-published": "true",
    "needs.container.result": "success",
    "needs.container.outputs.artifact-published": "true",
}


def job(workflow, name):
    return re.split(r"\n  [a-z][a-z-]*:\n", workflow.split(f"\n  {name}:\n", 1)[1], 1)[0]


def publication_script(workflow):
    step = workflow.split("      - name: Verify selected package registries\n", 1)[1]
    lines = []
    for line in step.split("        run: |\n", 1)[1].splitlines():
        if line and not line.startswith("          "):
            break
        lines.append(line)
    return textwrap.dedent("\n".join(lines))


def publication(workflow, **overrides):
    env = {
        **os.environ,
        "REGISTRY": "both", "MONOREPO": "false",
        "NPM_PUBLISHED": "true", "GITHUB_PUBLISHED": "true",
        "BUILD_RESULTS": "", "REQUIRE_PLAN": "false", "PLANNED_PACKAGES": "",
        **overrides,
    }
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "output"
        result = subprocess.run(
            [sys.executable, "-c", publication_script(workflow)],
            env={**env, "GITHUB_OUTPUT": str(output)}, capture_output=True, text=True,
        )
        values = dict(line.split("=", 1) for line in output.read_text().splitlines()) if output.exists() else {}
    return result, values.get("all-selected-registries-published", "false")


def permits(workflow, name, cancelled=False, **overrides):
    """Evaluate the workflow's actual boolean condition for controlled fixtures."""
    expression = re.search(r"^    if: \$\{\{ (.+) \}\}$", job(workflow, name), re.M)[1]
    return evaluate(expression, {**BASE, **overrides}, cancelled)


def evaluate(expression, values, cancelled=False):
    expression = re.sub(r"\b(?:inputs|needs|steps)\.[\w.-]+", lambda match: repr(values[match[0]]), expression)
    expression = expression.replace("cancelled()", repr(cancelled)).replace("always()", "True")
    expression = expression.replace("&&", " and ").replace("||", " or ")
    expression = re.sub(r"!(?!=)", "not ", expression).strip()
    return eval(expression, {"__builtins__": {}}, {})


def package(name="@test/one", version="1.2.3", **overrides):
    return {"name": name, "version": version, "result": "success",
            "npm-published": "true", "github-published": "true", **overrides}


class ReleaseGates(unittest.TestCase):
    def test_every_selected_registry_is_required(self):
        for name, workflow in WORKFLOWS.items():
            for registry, npm, github in itertools.product(
                ("npm", "github", "both"), ("true", "false", "", "dry-run"), ("true", "false", "", "dry-run")
            ):
                with self.subTest(workflow=name, registry=registry, npm=npm, github=github):
                    result, complete = publication(workflow, REGISTRY=registry, NPM_PUBLISHED=npm, GITHUB_PUBLISHED=github)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    expected = (registry == "github" or npm == "true") and (registry == "npm" or github == "true")
                    self.assertEqual(complete, str(expected).lower())

    def test_monorepo_requires_every_package_and_planned_version(self):
        plan = [package(), package("@test/two", "4.5.6")]
        cases = [
            (plan, True),
            (list(reversed(plan)), True),
            ([plan[0]], False),
            ([*plan, package("@test/extra")], False),
            ([plan[0], package("@test/two", "4.5.5")], False),
            ([plan[0], package("@test/two", "4.5.6", **{"npm-published": "false"})], False),
            ([plan[0], package("@test/two", "4.5.6", **{"github-published": "false"})], False),
            ([plan[0], package("@test/two", "4.5.6", result="failed")], False),
            ([*plan, plan[0]], False),
            ([plan[0], package(version="4.5.6")], False),
            ([], False),
        ]
        for name, workflow in WORKFLOWS.items():
            for results, expected in cases:
                with self.subTest(workflow=name, results=results):
                    result, complete = publication(workflow, MONOREPO="true", REQUIRE_PLAN="true",
                                                   PLANNED_PACKAGES=json.dumps(plan), BUILD_RESULTS=json.dumps(results))
                    if expected:
                        self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(complete, str(expected).lower())

    def test_monorepo_registry_selection_without_plan(self):
        for name, workflow in WORKFLOWS.items():
            for registry in ("npm", "github", "both"):
                for failed_registry in ("npm", "github"):
                    with self.subTest(workflow=name, registry=registry, failed=failed_registry):
                        results = [package(**{failed_registry + "-published": "false"})]
                        result, complete = publication(workflow, MONOREPO="true", REGISTRY=registry,
                                                       BUILD_RESULTS=json.dumps(results))
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(complete, str(registry not in ("both", failed_registry)).lower())

    def test_invalid_or_empty_evidence_never_completes(self):
        for name, workflow in WORKFLOWS.items():
            for raw in ("", "[]", "null", "{}", "broken", '[{"name":"a"}]', '[null]'):
                with self.subTest(workflow=name, raw=raw):
                    _, complete = publication(workflow, MONOREPO="true", BUILD_RESULTS=raw)
                    self.assertEqual(complete, "false")
                    _, complete = publication(workflow, MONOREPO="true", REQUIRE_PLAN="true",
                                              PLANNED_PACKAGES=raw, BUILD_RESULTS=json.dumps([package()]))
                    self.assertEqual(complete, "false")
            for plan in ([package(), package()], [package(), package(version="9.9.9")]):
                result, complete = publication(workflow, MONOREPO="true", REQUIRE_PLAN="true",
                                               PLANNED_PACKAGES=json.dumps(plan), BUILD_RESULTS=json.dumps([package()]))
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(complete, "false")
            result, complete = publication(workflow, REGISTRY="unknown")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(complete, "false")

    def test_intentional_build_skip_blocks_release_without_evidence_failure(self):
        for name, workflow in WORKFLOWS.items():
            with self.subTest(workflow=name):
                step = workflow.split("      - name: Verify selected package registries\n", 1)[1]
                condition = re.search(r"^        if: \$\{\{ (.+) \}\}$", step, re.M)[1]
                self.assertFalse(evaluate(condition, {"steps.package.outputs.build-skipped": "true"}))
                for build_skipped in ("false", ""):
                    self.assertTrue(evaluate(condition, {"steps.package.outputs.build-skipped": build_skipped}))
                # A skipped evidence step leaves the job output false. The primitive
                # succeeds intentionally, but neither an old release plan nor the
                # aggregate publication flag may enable the GitHub Release.
                self.assertIn(
                    "all-selected-registries-published: ${{ steps.publication.outputs.all-selected-registries-published || 'false' }}",
                    job(workflow, "package"),
                )
                self.assertFalse(permits(workflow, "release", **{
                    "needs.package.result": "success",
                    "needs.package.outputs.all-selected-registries-published": "false",
                }))
                # Missing evidence from an actual attempt must still fail the gate.
                result, complete = publication(workflow, MONOREPO="true", REQUIRE_PLAN="true",
                                               PLANNED_PACKAGES=json.dumps([package()]), BUILD_RESULTS="")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(complete, "false")

    def test_security_failures_block_every_side_effect(self):
        for name, workflow in WORKFLOWS.items():
            jobs = ("source-finalize", "package", "container") if name == "app.yml" else ("source-finalize", "package")
            for target in jobs:
                with self.subTest(workflow=name, job=target):
                    needs = re.search(r"^    needs: \[(.+)\]$", job(workflow, target), re.M)[1].split(", ")
                    self.assertIn("codeql", needs)
                    self.assertIn("ci-gate", needs)
                    self.assertTrue(permits(workflow, target))
                    self.assertFalse(permits(workflow, target, cancelled=True))
                    for result in ("failure", "cancelled", "skipped"):
                        self.assertFalse(permits(workflow, target, **{"needs.ci-gate.result": result}))
                        self.assertFalse(permits(workflow, target, **{"needs.codeql.result": result}))
                    for disabled in ({"inputs.enable-codeql": False}, {"needs.ci-gate.outputs.resolved-codeql-languages": ""}):
                        self.assertTrue(permits(workflow, target, **{"needs.codeql.result": "skipped", **disabled}))
                        for result in ("failure", "cancelled"):
                            self.assertFalse(permits(workflow, target, **{"needs.codeql.result": result, **disabled}))
                    if target != "source-finalize":
                        # Non-main publication cannot bypass security either.
                        self.assertFalse(permits(workflow, target, **{
                            "needs.context.outputs.is-main": "false", "needs.codeql.result": "failure",
                        }))

    def test_release_requires_job_success_and_complete_evidence(self):
        for name, workflow in WORKFLOWS.items():
            self.assertTrue(permits(workflow, "release"))
            self.assertFalse(permits(workflow, "release", cancelled=True))
            for result, complete in itertools.product(
                ("success", "failure", "cancelled", "skipped"), ("true", "false", ""),
            ):
                with self.subTest(workflow=name, result=result, complete=complete):
                    self.assertEqual(permits(workflow, "release", **{
                        "needs.package.result": result,
                        "needs.package.outputs.all-selected-registries-published": complete,
                    }), result == "success" and complete == "true")
            for target in ("package", "release"):
                self.assertIn("needs.source-finalize.outputs.finalized-sha", job(workflow, target))
            section = job(workflow, "package")
            self.assertIn("artifact-published: ${{ steps.package.outputs.artifact-published || 'false' }}", section)
            self.assertIn("all-selected-registries-published: ${{ steps.publication.outputs.all-selected-registries-published || 'false' }}", section)
            for output in ("npm-published", "github-published", "build-results"):
                self.assertIn("steps.package.outputs." + output, section)
            self.assertIn("needs.version-plan.outputs.planned-packages-updated", section)
            self.assertIn("shell: python", section)


if __name__ == "__main__":
    unittest.main()
