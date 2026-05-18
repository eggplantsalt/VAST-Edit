# VAST-Edit Implementation Report

## Implemented Files

Core package:

- `vast_edit/vast_edit/schema.py`
- `vast_edit/vast_edit/config.py`
- `vast_edit/vast_edit/io_utils.py`
- `vast_edit/vast_edit/text_utils.py`
- `vast_edit/vast_edit/video_io.py`
- `vast_edit/vast_edit/builder.py`
- `vast_edit/vast_edit/overlays/base.py`
- `vast_edit/vast_edit/overlays/spatial_text.py`
- `vast_edit/vast_edit/overlays/spatial_target.py`
- `vast_edit/vast_edit/overlays/temporal_chain.py`
- `vast_edit/vast_edit/eval/judge_tasks.py`
- `vast_edit/vast_edit/eval/metrics.py`
- `vast_edit/vast_edit/eval/aggregation.py`

Scripts:

- `vast_edit/scripts/build_pilot.py`
- `vast_edit/scripts/inspect_manifest.py`
- `vast_edit/scripts/validate_manifest.py`
- `vast_edit/scripts/export_model_inputs.py`
- `vast_edit/scripts/build_judge_tasks.py`
- `vast_edit/scripts/aggregate_scores.py`

Configs and examples:

- `vast_edit/configs/pilot_v01.yaml`
- `vast_edit/configs/attack_templates.yaml`
- `vast_edit/configs/judge_prompts.yaml`
- `vast_edit/examples/input_manifest.example.jsonl`
- `vast_edit/examples/judge_scores.example.jsonl`

Docs:

- `vast_edit/README.md`
- `vast_edit/PROGRESS.md`
- `vast_edit/docs/DATA_SCHEMA.md`
- `vast_edit/docs/ATTACK_TAXONOMY.md`
- `vast_edit/docs/LOCAL_DEVELOPMENT.md`
- `vast_edit/docs/SERVER_RUNBOOK.md`
- `vast_edit/docs/MODEL_OUTPUT_CONVENTION.md`

## Main Entry Points

- Build pilot videos and `samples.jsonl`:
  `python vast_edit/scripts/build_pilot.py ...`
- Inspect generated samples:
  `python vast_edit/scripts/inspect_manifest.py ...`
- Validate input or sample manifests:
  `python vast_edit/scripts/validate_manifest.py ...`
- Export video editing model inputs:
  `python vast_edit/scripts/export_model_inputs.py ...`
- Build future judge task files:
  `python vast_edit/scripts/build_judge_tasks.py ...`
- Aggregate already-produced judge scores:
  `python vast_edit/scripts/aggregate_scores.py ...`

All scripts include minimal `sys.path` handling so they are intended to be callable from the IVEBench repository root as `python vast_edit/scripts/SCRIPT_NAME.py ...`.

## Data Flow

1. Human prepares `input_manifest.jsonl`.
2. `build_pilot.py` reads the input manifest and renders four variants:
   `clean`, `benign`, `attack`, and `scrambled`.
3. The builder writes:
   - `videos/{variant}/{sample_id}.mp4`
   - `metadata/samples.jsonl`
   - `metadata/input_manifest.snapshot.jsonl`
   - `logs/build_summary.json`
4. `export_model_inputs.py` converts `samples.jsonl` into `model_inputs.jsonl`.
5. An external video editing model reads `model_inputs.jsonl` and saves outputs under:
   `model_outputs/MODEL_NAME/{variant}/{sample_id}.mp4`.
6. `build_judge_tasks.py` creates single-video and pairwise judge task JSONL files.
7. An external MLLM or human process produces `judge_scores.jsonl`.
8. `aggregate_scores.py` computes AEC, UER, CALS, and quality pass rate.

## Known Assumptions

- `sample_id`, `base_id`, `variant`, `attack_family`, `authorized_instruction`, `target_prompt`, `expected_behavior`, and `safety_rule` are the canonical fields connecting all stages.
- Input manifests may use `id` or `sample_id`; `InputExample.from_dict()` accepts `sample_id` as an alias for `id`.
- Variant names are globally fixed as `clean`, `benign`, `attack`, and `scrambled`.
- Attack family names are globally fixed as `spatial_text_cue`, `spatial_target_cue`, and `temporal_cue_chain`.
- Runtime video generation expects OpenCV, NumPy, and PyYAML on the server.
- Local code-agent work has not executed scripts or validated runtime imports.

## Polish Pass

- Documentation stale wording was fixed: README now describes VAST-Edit v0.1 as functional but not server-validated code, not an empty scaffold.
- `attack_templates.yaml` comments were corrected: the builder reads templates, resolves them into `OverlayParams`, and renderers consume `OverlayParams`.
- Template selection is now deterministic and diversified:
  - `template_name` in input metadata selects by template name;
  - `template_index` selects by index;
  - otherwise the builder uses a stable hash of input ID and attack family;
  - all four variants for the same input example and attack family use the same selected template.
- A base-manifest expansion tool was added:
  - `vast_edit/vast_edit/manifest_expansion.py`
  - `vast_edit/scripts/expand_manifest.py`
  - `vast_edit/examples/base_manifest.example.jsonl`

## Research-Correctness Fix

- Attack and scrambled overlay text now defaults to the input manifest's `attack_intent`.
- `template.default_text` is now fallback only, so templates do not silently override the benchmark's recorded unauthorized visual intent.
- `extra.overlay_text` can explicitly override rendered overlay text when a study needs rendered text to differ from `attack_intent`.
- Benign variants use template benign text or harmless fallback text; they do not reuse `attack_intent`.
- Clean variants do not render attack overlays.
- `overlay_params.extra` records `text_source`, `template_default_text`, and `attack_intent_text` for auditability.

## Functionality Completeness Check

Static review status: VAST-Edit v0.1 is not an empty scaffold. It contains functional,未实测 benchmark code for data generation, model-input export, judge-task export, and offline aggregation.

Module-level check:

| Module | Static completeness |
| --- | --- |
| `schema.py` | Real dataclasses for `InputExample`, `OverlayParams`, and `SampleRecord`; includes `to_dict()`, `from_dict()`, and required-field errors. |
| `config.py` | Real YAML loading with lazy PyYAML import and clear missing-dependency error. |
| `io_utils.py` | Real JSONL read/write, manifest loading, sample writing, directory creation, and stable ID hashing. |
| `text_utils.py` | Real text normalization, benign text selection, and semantic scrambling helper. |
| `video_io.py` | Real OpenCV/NumPy video probe, sequential RGB frame read, RGB frame write, copy, and resolution helpers. |
| `overlays/base.py` | Real alpha blending and drawing primitives for text boxes, arrows, boxes, circles, polylines, UI panels, positions, and clamped points. |
| `overlays/spatial_text.py` | Real renderer for `clean`, `benign`, `attack`, and `scrambled` spatial text variants. |
| `overlays/spatial_target.py` | Real renderer for `clean`, `benign`, `attack`, and `scrambled` target cues with arrow/box/circle/highlight support. |
| `overlays/temporal_chain.py` | Real renderer for fragmented text, progressive target binding, and motion trajectory chains. |
| `builder.py` | Real pilot orchestration: reads input manifest, builds overlay params, copies clean videos by default, renders other variants, writes videos, `samples.jsonl`, manifest snapshot, and build summary. |
| `scripts/build_pilot.py` | Real argparse CLI calling `build_pilot_dataset`; includes repo-root import path handling. |
| `scripts/inspect_manifest.py` | Real samples manifest inspection with variant/family counts and missing path count. |
| `scripts/validate_manifest.py` | Real lightweight field validation for input and samples modes. |
| `scripts/export_model_inputs.py` | Real conversion from `samples.jsonl` to `model_inputs.jsonl`. |
| `eval/judge_tasks.py` | Real single-video and pairwise judge task construction; no MLLM calls. |
| `scripts/build_judge_tasks.py` | Real argparse CLI producing single and pairwise judge task JSONL files. |
| `eval/metrics.py` | Real pure-Python AEC, UER, CALS, TPR-like proxy, and quality pass helpers; no pandas. |
| `eval/aggregation.py` | Real judge score aggregation and JSON/CSV writers. |
| `scripts/aggregate_scores.py` | Real argparse CLI producing `summary.json`, `per_sample_scores.csv`, and `per_group_cals.csv`. |

No `pass`, placeholder-only TODO implementation, or intentional `NotImplementedError` remains in the core v0.1 functional path.

## Things Not Implemented Yet

- Real video editing model inference.
- Real MLLM or human judge integration.
- Runtime validation on actual videos.
- Unit tests or smoke tests.
- IVEBench metric integration.
- A polished result leaderboard or report generator.
- Server-specific dependency installation instructions.

## Server-side First Debug Checklist

1. Create a tiny input manifest with one short video and one attack family.
2. Run `validate_manifest.py --mode input`.
3. Run `build_pilot.py --limit 1 --overwrite`.
4. Confirm `videos/clean`, `videos/benign`, `videos/attack`, and `videos/scrambled` each contain one `.mp4`.
5. Run `inspect_manifest.py` on `metadata/samples.jsonl`.
6. Run `validate_manifest.py --mode samples`.
7. Run `export_model_inputs.py`.
8. Manually check one `model_inputs.jsonl` row and confirm `authorized_instruction` is the only model command.
9. Run a small external model inference job and save outputs using exact `sample_id` filenames.
10. Run `build_judge_tasks.py`.
11. Create a tiny hand-written `judge_scores.jsonl` following the example schema.
12. Run `aggregate_scores.py` and inspect `summary.json`.

## Recommended Next Human Actions

- Push this VAST-Edit extension to the server or a branch where server dependencies are available.
- Run the first one-video pilot with `--limit 1`.
- Debug OpenCV codec behavior and output video readability on the server.
- Confirm that model input manifests match the target editing model's expected input format.
- Decide the first MLLM or human judging protocol and score calibration rubric.
- After one successful end-to-end dry run, expand to a small balanced pilot across all three attack families.
