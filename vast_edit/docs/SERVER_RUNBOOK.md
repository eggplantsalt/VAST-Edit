# Server Runbook

This runbook is for a future headless server run. The local code-agent workflow should not execute these commands unless explicitly requested.

All paths below are templates. Replace `/path/to/IVEBench`, `/path/to/manifests`, `/path/to/vast_edit_outputs`, and `MODEL_NAME` with real server paths and method names before running.

## 1. Prepare Workspace

```bash
cd /path/to/IVEBench
mkdir -p /path/to/vast_edit_outputs/pilot_v01
```

Install runtime dependencies on the server environment only, according to the server's package policy. The pilot builder expects OpenCV, NumPy, and PyYAML at runtime.

## 2. Prepare Base Manifest

Create a base JSONL manifest with one source video and authorized instruction per line. Use the schema in `vast_edit/docs/DATA_SCHEMA.md`.

Example path:

```text
/path/to/manifests/vast_edit_base_manifest.jsonl
```

Each row should include fields such as:

```text
id or sample_id
source_video
source_video_name
source_prompt
authorized_instruction
target_prompt
attack_family
attack_intent
attack_intents
attack_families
expected_behavior
safety_rule
```

## 3. Expand Base Manifest

This creates one expanded input row per attack family.

```bash
python vast_edit/scripts/expand_manifest.py \
  --base_manifest /path/to/manifests/vast_edit_base_manifest.jsonl \
  --output_manifest /path/to/manifests/vast_edit_input_manifest.expanded.jsonl
```

## 4. Validate Expanded Input Manifest

This checks JSONL fields only. It does not read video contents.

```bash
python vast_edit/scripts/validate_manifest.py \
  /path/to/manifests/vast_edit_input_manifest.expanded.jsonl \
  --mode input
```

## 5. Build Pilot Variants

```bash
python vast_edit/scripts/build_pilot.py \
  --input_manifest /path/to/manifests/vast_edit_input_manifest.expanded.jsonl \
  --output_dir /path/to/vast_edit_outputs/pilot_v01 \
  --config vast_edit/configs/pilot_v01.yaml \
  --templates vast_edit/configs/attack_templates.yaml \
  --limit 20 \
  --seed 0 \
  --overwrite
```

Expected outputs:

```text
/path/to/vast_edit_outputs/pilot_v01/
  videos/
    clean/
    benign/
    attack/
    scrambled/
  metadata/
    samples.jsonl
    input_manifest.snapshot.jsonl
  logs/
    build_summary.json
```

## 6. Inspect Generated Samples

This checks `samples.jsonl` and whether declared output paths exist. It does not decode videos.

```bash
python vast_edit/scripts/inspect_manifest.py \
  /path/to/vast_edit_outputs/pilot_v01/metadata/samples.jsonl
```

## 7. Validate Generated Samples

```bash
python vast_edit/scripts/validate_manifest.py \
  /path/to/vast_edit_outputs/pilot_v01/metadata/samples.jsonl \
  --mode samples
```

## 8. Prepare Video Editing Model Inputs

For each row in `metadata/samples.jsonl`, pass `output_video` as the model input video and `authorized_instruction` as the only text instruction.

Generate a model input manifest:

```bash
python vast_edit/scripts/export_model_inputs.py \
  --samples_jsonl /path/to/vast_edit_outputs/pilot_v01/metadata/samples.jsonl \
  --model_name MODEL_NAME \
  --output_jsonl /path/to/vast_edit_outputs/pilot_v01/metadata/model_inputs.jsonl \
  --model_output_root /path/to/vast_edit_outputs/pilot_v01/model_outputs/MODEL_NAME
```

The variant folders can be used for controlled evaluation:

```text
videos/clean/
videos/benign/
videos/attack/
videos/scrambled/
```

Do not append visual cue text, UI labels, arrows, subtitles, or target markers from the video to the model prompt.

## 9. Run External Video Editing Model

Run the target video editing method outside VAST-Edit. The exact command is model-specific.

Template:

```bash
python /path/to/model_inference.py \
  --input_manifest /path/to/vast_edit_outputs/pilot_v01/metadata/model_inputs.jsonl \
  --output_root /path/to/vast_edit_outputs/pilot_v01/model_outputs/MODEL_NAME
```

Expected output convention:

```text
/path/to/vast_edit_outputs/pilot_v01/model_outputs/MODEL_NAME/
  clean/
  benign/
  attack/
  scrambled/
```

Each output filename should be exactly `sample_id.mp4`.

## 10. Create Judge Tasks

```bash
python vast_edit/scripts/build_judge_tasks.py \
  --samples_jsonl /path/to/vast_edit_outputs/pilot_v01/metadata/samples.jsonl \
  --model_name MODEL_NAME \
  --model_output_root /path/to/vast_edit_outputs/pilot_v01/model_outputs/MODEL_NAME \
  --judge_prompts vast_edit/configs/judge_prompts.yaml \
  --output_dir /path/to/vast_edit_outputs/pilot_v01/judge_tasks/MODEL_NAME
```

This creates task definitions only. It does not call an MLLM or human labeling service.

## 11. Collect Judge Scores

After a future MLLM or human judging step, save results as:

```text
/path/to/vast_edit_outputs/pilot_v01/judge_results/MODEL_NAME/judge_scores.jsonl
```

The expected fields are documented in `vast_edit/docs/DATA_SCHEMA.md`.

## 12. Aggregate Scores

```bash
python vast_edit/scripts/aggregate_scores.py \
  --judge_scores /path/to/vast_edit_outputs/pilot_v01/judge_results/MODEL_NAME/judge_scores.jsonl \
  --output_dir /path/to/vast_edit_outputs/pilot_v01/metrics/MODEL_NAME \
  --quality_threshold 3.0 \
  --score_threshold 3.0
```

Expected outputs:

```text
/path/to/vast_edit_outputs/pilot_v01/metrics/MODEL_NAME/
  summary.json
  per_sample_scores.csv
  per_group_cals.csv
```

## 13. Future Work

Future stages will add real MLLM or human judge adapters. The current repository only builds task files and aggregates already-produced judge scores.
