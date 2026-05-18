# Local Development

Local development for VAST-Edit is code-first and lightweight.

The local code-agent environment is intended for:

- writing documentation;
- editing configuration files;
- implementing small, reviewable utilities;
- preparing scripts that will later run on a server;
- manually inspecting schemas and code structure.

Do not use the local environment for dependency-heavy experiments.

## Local Prohibitions

- Do not run video editing model inference.
- Do not run MLLM judge inference.
- Do not download model weights.
- Do not download large benchmark datasets.
- Do not run GPU workloads.
- Do not run large video rendering jobs.
- Do not run expensive tests or smoke tests unless explicitly requested.
- Do not attempt to read or write real videos locally unless a task explicitly asks for it.

## Runtime Dependencies

Some VAST-Edit modules are written against runtime dependencies that may not be installed locally:

- `cv2` / OpenCV for video IO and overlay drawing;
- `numpy` for frame arrays;
- `pyyaml` for YAML config loading.

These dependencies should be installed and verified on the server or runtime environment, not during local code-agent scaffolding. Local edits may add imports for these runtime modules, but should not execute them unless explicitly requested.

## Preferred Local Workflow

1. Make small edits under `vast_edit/`.
2. Keep configuration and manifests human-readable.
3. Use relative paths in examples.
4. Keep scripts compatible with headless server execution.
5. Document command templates without assuming local dependencies are installed.
6. Leave dependency and video IO validation for the server runbook stage.
