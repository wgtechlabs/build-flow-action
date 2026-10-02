"""Exercise the workflow's actual inline image resolver and publication guard."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


WORKFLOW = (Path(__file__).resolve().parents[1] / ".github/workflows/app.yml").read_text()
DEFAULTS = {
    "image-name": "legacy-app",
    "dockerfile": "./Dockerfile",
    "context": ".",
    "build-args": "MODE=shared\nVERSION=1",
    "platforms": "linux/amd64",
    "release-platforms": "linux/amd64,linux/arm64",
}


def step_run(name):
    step = WORKFLOW.split(f"      - name: {name}\n", 1)[1]
    script = step.split("        run: |\n", 1)[1]
    lines = []
    for line in script.splitlines():
        if line and not line.startswith("          "):
            break
        lines.append(line)
    return textwrap.dedent("\n".join(lines))


def resolve(raw, defaults=DEFAULTS):
    env = {**os.environ, "IMAGES": raw}
    env.update({"DEFAULT_" + key.upper().replace("-", "_"): value for key, value in defaults.items()})
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "output"
        env["GITHUB_OUTPUT"] = str(output)
        result = subprocess.run(
            [sys.executable, "-c", step_run("Resolve container images")],
            env=env, capture_output=True, text=True, check=False,
        )
        values = dict(line.split("=", 1) for line in output.read_text().splitlines()) if output.exists() else {}
    return result, values


class ContainerImages(unittest.TestCase):
    def test_legacy_single_image(self):
        for raw in ("", " \n "):
            with self.subTest(raw=raw):
                result, outputs = resolve(raw)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(outputs["images"]), [{**DEFAULTS, "scan-suffix": ""}])
                self.assertEqual(outputs["multiple-images"], "false")

    def test_multiple_images_inherit_and_override_defaults(self):
        images = [
            {"image-name": "app"},
            {"image-name": "browser", "dockerfile": "browser/Dockerfile", "context": "browser",
             "build-args": "SERVICE=browser\nSPECIAL='value'", "platforms": "linux/arm64",
             "release-platforms": "linux/arm64"},
        ]
        result, outputs = resolve(json.dumps(images))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(outputs["images"]), [
            {**DEFAULTS, **image, "scan-suffix": f"-image-{index}"}
            for index, image in enumerate(images)
        ])
        self.assertEqual(outputs["multiple-images"], "true")

    def test_explicit_empty_optional_fields_do_not_inherit(self):
        image = {"image-name": "namespace/app", "build-args": "", "release-platforms": ""}
        result, outputs = resolve(json.dumps([image]))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(outputs["images"]), [{**DEFAULTS, **image, "scan-suffix": ""}])
        self.assertEqual(outputs["multiple-images"], "false")

    def test_matrix_capacity(self):
        images = [{"image-name": f"app-{index}"} for index in range(256)]
        result, outputs = resolve(json.dumps(images))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(outputs["images"])), 256)

    def test_resolved_output_size_limit(self):
        raw = json.dumps([{"image-name": f"app-{index}"} for index in range(256)])
        for args, valid in (("ARG=" + "x" * 1000, True), ("ARG=" + "x" * 4096, False),
                            ("ARG=" + "\U0001f680" * 500, False)):
            with self.subTest(valid=valid, argument_length=len(args)):
                result, outputs = resolve(raw, {**DEFAULTS, "build-args": args})
                if valid:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertLessEqual(len(outputs["images"].encode("utf-16-le")), 900 * 1024)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("resolved images exceed 900 KiB", result.stderr)
                    self.assertEqual(outputs, {})

    def test_unqualified_names(self):
        images = [{"image-name": name} for name in ("app.backend", "namespace/app", "org/team/app", "localhost")]
        result, outputs = resolve(json.dumps(images))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([image["image-name"] for image in json.loads(outputs["images"])],
                         [image["image-name"] for image in images])

    def test_invalid_definitions_fail_without_outputs(self):
        invalid = {
            "invalid JSON": "[",
            "object": "{}",
            "null": "null",
            "string": '"app"',
            "empty array": "[]",
            "over capacity": json.dumps([{"image-name": f"app-{index}"} for index in range(257)]),
            "non-object entry": '["app"]',
            "null entry": "[null]",
            "unknown field": '[{"image-name":"app","target":"app"}]',
            "missing name": "[{}]",
            "duplicate names": '[{"image-name":"app"},{"image-name":"app"}]',
        }
        for value in (None, 1, True, [], {}):
            invalid[f"nonstring value {value!r}"] = json.dumps([{"image-name": "app", "build-args": value}])
        for name in ("", "App", " app", "app ", "app:latest", "app@sha256:123", "/app", "app/", "a//b",
                     "ghcr.io/org/app", "docker.io/org/app", "registry.example/app", "localhost/app", "localhost:5000/app"):
            invalid[f"invalid name {name!r}"] = json.dumps([{"image-name": name}])
        for field in ("dockerfile", "context", "platforms"):
            for value in ("", " \n "):
                invalid[f"empty {field} {value!r}"] = json.dumps([{"image-name": "app", field: value}])
        for name, raw in invalid.items():
            with self.subTest(name=name):
                result, outputs = resolve(raw)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("::error::Invalid container-images:", result.stderr)
                self.assertEqual(outputs, {})

    def test_every_matrix_child_must_publish(self):
        for published in ("true", "false", ""):
            with self.subTest(published=published):
                result = subprocess.run(
                    ["bash", "-e", "-c", step_run("Require every image to publish")],
                    env={**os.environ, "ARTIFACT_PUBLISHED": published},
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode == 0, published == "true")

    def test_matrix_wiring_and_aggregate_output(self):
        container = WORKFLOW.split("\n  container:\n", 1)[1].split("\n  artifact-summary:\n", 1)[0]
        for required in (
            "fail-fast: false",
            "image: ${{ fromJSON(needs.context.outputs.container-images) }}",
            "ref: ${{ needs.source-finalize.outputs.finalized-sha || github.sha }}",
            "planned-version-tag: ${{ needs.context.outputs.is-main == 'true' && needs.version-plan.outputs.planned-version-tag || '' }}",
            "if: ${{ needs.context.outputs.multiple-images == 'true' && inputs.container-push-enabled }}",
        ):
            self.assertIn(required, container)
        for field in DEFAULTS:
            self.assertIn(f"{field}: ${{{{ matrix.image.{field} }}}}", container)
        for category in ("source", "dockerfile", "image"):
            self.assertIn(f"sarif-category-{category}: ${{{{ inputs.container-sarif-category-{category} }}}}${{{{ matrix.image.scan-suffix }}}}", container)
        self.assertIn("value: ${{ jobs.artifact-summary.outputs.container-artifact-published }}", WORKFLOW)
        self.assertIn("container-artifact-published: ${{ needs.container.result == 'success' && needs.container.outputs.artifact-published || 'false' }}", WORKFLOW)
        self.assertIn("CONTAINER_PUBLISHED: ${{ needs.container.result == 'success' && needs.container.outputs.artifact-published || 'false' }}", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
