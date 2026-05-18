# VAST-Edit Progress

## Status

v0.1 functional code writing is complete at the static review level. The repository now contains concrete, non-placeholder code for schema handling, config loading, JSONL IO, video IO, overlay rendering, pilot dataset building, model input export, judge task export, and offline score aggregation.

No runtime validation has been performed in this local environment. No scripts, tests, video rendering, model inference, MLLM judging, or score aggregation have been executed.

## Completed

- Created the isolated `vast_edit/` extension directory.
- Added documentation for schema, taxonomy, local development, server workflow, and model output conventions.
- Added v0.1 configuration files for pilot settings, attack templates, and judge prompts.
- Added example input manifest and judge score JSONL files.
- Implemented lightweight dataclass schemas in `vast_edit/vast_edit/schema.py`.
- Implemented explicit YAML config loading helpers in `vast_edit/vast_edit/config.py`.
- Implemented JSONL IO, manifest loading, sample writing, directory creation, and stable ID helpers in `vast_edit/vast_edit/io_utils.py`.
- Implemented small overlay text utilities in `vast_edit/vast_edit/text_utils.py`.
- Implemented OpenCV-based video IO helpers in `vast_edit/vast_edit/video_io.py`.
- Implemented RGB overlay drawing primitives in `vast_edit/vast_edit/overlays/base.py`.
- Implemented v0.1 renderer modules:
  - `vast_edit/vast_edit/overlays/spatial_text.py`
  - `vast_edit/vast_edit/overlays/spatial_target.py`
  - `vast_edit/vast_edit/overlays/temporal_chain.py`
- Implemented pilot dataset orchestration in `vast_edit/vast_edit/builder.py`.
- Added CLI entrypoint templates:
  - `vast_edit/scripts/build_pilot.py`
  - `vast_edit/scripts/inspect_manifest.py`
  - `vast_edit/scripts/validate_manifest.py`
  - `vast_edit/scripts/export_model_inputs.py`
  - `vast_edit/scripts/build_judge_tasks.py`
  - `vast_edit/scripts/aggregate_scores.py`
- Implemented judge task construction in `vast_edit/vast_edit/eval/judge_tasks.py`.
- Implemented offline metric helpers in `vast_edit/vast_edit/eval/metrics.py`.
- Implemented score aggregation and CSV/JSON writers in `vast_edit/vast_edit/eval/aggregation.py`.
- Added a TPR-like proxy based on pairwise judge rows where the attack output is more aligned with the unauthorized cue than controls.
- Fixed stale README and template comments from the early scaffold phase.
- Added deterministic diversified template selection in `builder.py`.
- Added base-manifest expansion via `vast_edit/vast_edit/manifest_expansion.py` and `vast_edit/scripts/expand_manifest.py`.
- Added `vast_edit/examples/base_manifest.example.jsonl`.
- Fixed research-correctness issue in builder text selection: attack/scrambled overlay text now defaults to input `attack_intent`, template default text is fallback only, and `text_source` is recorded for auditability.
- Updated README, runbook, schema docs, attack taxonomy, model output convention, and implementation report.

## Consistency Notes

- Variant names are consistently `clean`, `benign`, `attack`, and `scrambled`.
- Attack family names are consistently `spatial_text_cue`, `spatial_target_cue`, and `temporal_cue_chain`.
- `samples.jsonl`, `model_inputs.jsonl`, judge tasks, and judge scores are linked by `sample_id`, `base_id`, `variant`, `attack_family`, and `model_name`.
- Input manifest examples use `sample_id`; the loader accepts this as an alias for schema field `id`.
- Static completeness review found concrete implementations for all v0.1 modules. The next risk is runtime behavior, not empty scaffold code.

## Next Step

Push or copy the repository to a server/runtime environment and perform actual debugging with a tiny pilot:

1. Validate a one-row input manifest.
2. Build one pilot item with all four variants.
3. Inspect generated videos and `samples.jsonl`.
4. Export `model_inputs.jsonl`.
5. Run one external video editing model manually.
6. Build judge tasks.
7. Create a small manual `judge_scores.jsonl`.
8. Run aggregation and inspect the output metrics.

## Constraints

- Keep all extension work inside `vast_edit/`.
- Do not modify IVEBench original source unless explicitly approved.
- Do not run local GPU inference, download weights, or process large datasets during local code-agent development.
- Do not run local video IO, overlay rendering, model inference, MLLM judging, or score aggregation unless explicitly requested.
