# VAST-Edit Server Debug Report

## Run Metadata

- Current time: 2026-05-18 20:33 Asia/Shanghai
- Working directory: `/workspace/zy_workspace/VAST-Edit`
- Git branch: `vast-edit-v0.1`
- Commit hash: `4b6ec9e56c327590154056ca114c2aac0de6bd32`
- Remote: `origin https://gh.llkk.cc/https://github.com/eggplantsalt/VAST-Edit.git`
- Python version: `Python 3.13.11`
- OS: `Linux interactive31425 5.4.0-100-generic #113-Ubuntu SMP Thu Feb 3 18:43:29 UTC 2022 x86_64 GNU/Linux`
- GPU visibility: `GPU 0: NVIDIA GeForce RTX 4090`; GPU was recorded only and not used.
- Data root: `/opt/data/private/zy_data/VAST-Edit`
- Output root: `/opt/data/private/zy_data/VAST-Edit/outputs`
- Repository output symlink: `vast_edit_outputs -> /opt/data/private/zy_data/VAST-Edit/outputs`

## Planned Stages

1. Prepare directories and verify repository.
2. Read project context and maintain this server debug report.
3. Create a minimal Python virtual environment.
4. Run static compilation checks.
5. Build and validate a synthetic video debug pilot.
6. Generate contact sheets for visual overlay inspection.
7. Construct fake judge scores and validate aggregation.
8. Prepare a real one-video pilot if a suitable local source video exists.
9. Record final repository status, changes, outputs, and blockers.

## Stage Results

- Stage 0: Repository already existed at `/workspace/zy_workspace/VAST-Edit`; branch `vast-edit-v0.1` was present. Data directories were created or already present.
- Stage 1: Project context files were read: `PROJECT_CONTEXT.md`, `OVERVIEW.md`, `vast_edit/README.md`, `vast_edit/IMPLEMENTATION_REPORT.md`, `vast_edit/PROGRESS.md`, `vast_edit/docs/SERVER_RUNBOOK.md`, and `vast_edit/docs/DATA_SCHEMA.md`.
- Stage 2: Created or reused Python virtual environment at `/opt/data/private/zy_data/VAST-Edit/venvs/vast-edit-v01`.
  - Installed minimal dependencies only: `numpy-2.4.5`, `opencv-python-headless-4.13.0.92`, `pyyaml-6.0.3`, `tqdm-4.67.3`.
  - Added `vast_edit/requirements-minimal.txt` because it was not present.
  - No torch, transformers, diffusers, Qwen, video editing model dependency, model weight, or MLLM dependency was installed.
- Stage 3: `python -m compileall vast_edit` passed before runtime testing and passed again after code changes.
- Stage 4: Synthetic debug video and manifest were created under `/opt/data/private/zy_data/VAST-Edit/outputs/debug_synthetic`.
  - Source video: `/opt/data/private/zy_data/VAST-Edit/outputs/debug_synthetic/source_videos/synthetic_001.mp4`
  - Base manifest: `/opt/data/private/zy_data/VAST-Edit/outputs/debug_synthetic/base_manifest.jsonl`
  - Expanded manifest: `/opt/data/private/zy_data/VAST-Edit/outputs/debug_synthetic/input_manifest.expanded.jsonl`
  - Pilot output: `/opt/data/private/zy_data/VAST-Edit/outputs/debug_synthetic/pilot`
  - Generated samples: `12`
  - Variant distribution: `clean=3`, `benign=3`, `attack=3`, `scrambled=3`
  - Attack family distribution in samples: `spatial_text_cue=4`, `spatial_target_cue=4`, `temporal_cue_chain=4`
  - Model inputs: `/opt/data/private/zy_data/VAST-Edit/outputs/debug_synthetic/pilot/metadata/model_inputs.debug_model.jsonl`
  - Judge tasks: `/opt/data/private/zy_data/VAST-Edit/outputs/debug_synthetic/judge_tasks/debug_model`
  - Single-video judge tasks: `12`
  - Pairwise judge tasks: `3`
- Stage 5: Contact sheets were generated under `/opt/data/private/zy_data/VAST-Edit/outputs/debug_synthetic/debug_artifacts`.
  - Overview: `/opt/data/private/zy_data/VAST-Edit/outputs/debug_synthetic/debug_artifacts/contact_sheet_overview.png`
  - Per-family PNGs were generated for all three attack families.
  - Added reusable script `vast_edit/scripts/make_contact_sheet.py`.
  - Documented usage in `vast_edit/README.md` and `vast_edit/docs/SERVER_RUNBOOK.md`.
- Stage 6: Fake judge scores were constructed and aggregation passed.
  - Fake scores: `/opt/data/private/zy_data/VAST-Edit/outputs/debug_synthetic/judge_results/debug_model/judge_scores.fake.jsonl`
  - Metrics output: `/opt/data/private/zy_data/VAST-Edit/outputs/debug_synthetic/metrics/debug_model`
  - Outputs present: `summary.json`, `per_sample_scores.csv`, `per_group_cals.csv`
  - `overall_mean_cals`: `2.9`
  - `missing_cals_groups`: empty
- Stage 7: Real one-video pilot search was limited to requested locations:
  - `/opt/data/private/zy_data/VAST-Edit/source_videos`
  - `/opt/data/private/zy_data`
  - `/workspace/zy_workspace/VAST-Edit/videos`
  - `/workspace/zy_workspace/VAST-Edit/data`
  - `/mnt/data`
  - `/data`
  - Only synthetic debug outputs created during this run were found under the broad `/opt/data/private/zy_data` scan. No external real source video was found.
  - Result: `No real source video found. Synthetic pilot passed. Waiting for user-provided source video path.`

## Commands That Ultimately Succeeded

- `python -m compileall vast_edit`
- `python vast_edit/scripts/expand_manifest.py --base_manifest ... --output_manifest ...`
- `python vast_edit/scripts/validate_manifest.py --manifest ... --mode input`
- `python vast_edit/scripts/build_pilot.py --input_manifest ... --output_dir ... --config ... --templates ... --seed 0 --overwrite`
- `python vast_edit/scripts/inspect_manifest.py --samples_jsonl ...`
- `python vast_edit/scripts/validate_manifest.py --manifest ... --mode samples`
- `python vast_edit/scripts/export_model_inputs.py --samples_jsonl ... --model_name debug_model ...`
- `python vast_edit/scripts/build_judge_tasks.py --samples_jsonl ... --model_name debug_model ...`
- `python vast_edit/scripts/make_contact_sheet.py --samples_jsonl ... --output_dir ... --frame_index 8`
- `python vast_edit/scripts/aggregate_scores.py --judge_scores ... --output_dir ... --quality_threshold 3.0 --score_threshold 3.0`

## Failures Encountered And Fixes

- Failure: `validate_manifest.py` rejected the requested `--manifest` option and only accepted a positional manifest path.
  - Fix: Updated `vast_edit/scripts/validate_manifest.py` to accept either positional manifest path or `--manifest`.
- Failure: `inspect_manifest.py` rejected the requested `--samples_jsonl` option and only accepted a positional samples path.
  - Fix: Updated `vast_edit/scripts/inspect_manifest.py` to accept either positional samples path or `--samples_jsonl`.

## Modified Files

- `vast_edit/requirements-minimal.txt`: added minimal server runtime dependencies.
- `vast_edit/scripts/validate_manifest.py`: CLI compatibility fix for `--manifest`.
- `vast_edit/scripts/inspect_manifest.py`: CLI compatibility fix for `--samples_jsonl`.
- `vast_edit/scripts/make_contact_sheet.py`: new reusable contact sheet generator.
- `vast_edit/README.md`: documented contact sheet debug usage.
- `vast_edit/docs/SERVER_RUNBOOK.md`: documented contact sheet debug usage.
- `vast_edit/SERVER_DEBUG_REPORT.md`: this report.

## Repository Status At End

`git status --short`:

```text
 M vast_edit/README.md
 M vast_edit/docs/SERVER_RUNBOOK.md
 M vast_edit/scripts/inspect_manifest.py
 M vast_edit/scripts/validate_manifest.py
?? vast_edit/SERVER_DEBUG_REPORT.md
?? vast_edit/requirements-minimal.txt
?? vast_edit/scripts/make_contact_sheet.py
?? vast_edit_outputs
```

`git diff --stat` for tracked files:

```text
 vast_edit/README.md                    |  8 ++++++++
 vast_edit/docs/SERVER_RUNBOOK.md       | 11 +++++++++++
 vast_edit/scripts/inspect_manifest.py  |  9 +++++++--
 vast_edit/scripts/validate_manifest.py |  9 +++++++--
 4 files changed, 33 insertions(+), 4 deletions(-)
```

Note: `vast_edit_outputs` is an untracked symlink to `/opt/data/private/zy_data/VAST-Edit/outputs`.

## Final Timestamp

- Completed: 2026-05-18 20:39:32 CST +0800
