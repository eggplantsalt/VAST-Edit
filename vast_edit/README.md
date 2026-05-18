# VAST-Edit

VAST-Edit is a benchmark extension for studying Visual Authority Confusion in instruction-guided video editing models.

The research question is simple: when a user provides an editing instruction, does the model follow that authorized instruction, or does it accidentally treat visual content inside the source video as an instruction?

## Visual Authority Confusion

Visual Authority Confusion occurs when a video editing model gives command authority to non-authoritative visual content inside the source video. Examples include text, arrows, UI labels, subtitles, target markers, path traces, or other visual cues that appear in the video frames.

In VAST-Edit, the source video is editable content. The user text instruction is the authorized command. A model should edit what is in the video, not obey what is written or indicated inside the video.

## Current Status

VAST-Edit v0.1 currently provides functional but not yet server-validated code for:

- input manifest validation and base-manifest expansion;
- counterfactual video generation for `clean`, `benign`, `attack`, and `scrambled` variants;
- `spatial_text_cue`, `spatial_target_cue`, and `temporal_cue_chain` overlay renderers;
- model input export;
- judge task construction;
- offline score aggregation for AEC, UER, CALS, TPR-like proxy, and quality pass rate.

It still does not include video editing model inference, real MLLM judge execution, GPU execution, data download, weight download, or server-side runtime validation.

## Quickstart Template

The pilot builder is intended to run on a server/runtime environment with OpenCV, NumPy, and PyYAML installed. From the IVEBench repository root:

Prepare a base manifest following `vast_edit/docs/DATA_SCHEMA.md`. Each line should describe one source video and one authorized instruction. Then expand it into attack-family-specific records:

```bash
python vast_edit/scripts/expand_manifest.py \
  --base_manifest path/to/base_manifest.jsonl \
  --output_manifest vast_edit_outputs/input_manifest.expanded.jsonl
```

```bash
python vast_edit/scripts/validate_manifest.py \
  vast_edit_outputs/input_manifest.expanded.jsonl \
  --mode input
```

```bash
python vast_edit/scripts/build_pilot.py \
  --input_manifest vast_edit_outputs/input_manifest.expanded.jsonl \
  --output_dir vast_edit_outputs/pilot_v01 \
  --config vast_edit/configs/pilot_v01.yaml \
  --templates vast_edit/configs/attack_templates.yaml \
  --limit 20 \
  --seed 0 \
  --overwrite
```

```bash
python vast_edit/scripts/inspect_manifest.py \
  vast_edit_outputs/pilot_v01/metadata/samples.jsonl
```

```bash
python vast_edit/scripts/validate_manifest.py \
  vast_edit_outputs/pilot_v01/metadata/samples.jsonl \
  --mode samples
```

Create contact sheets for quick human inspection of rendered overlays. The
script writes the standard overview plus a temporal multi-frame sheet for
`temporal_cue_chain`, using renderer metadata such as `visible_frame_ranges`
when available:

```bash
python vast_edit/scripts/make_contact_sheet.py \
  --samples_jsonl vast_edit_outputs/pilot_v01/metadata/samples.jsonl \
  --output_dir vast_edit_outputs/pilot_v01/debug_artifacts
```

Renderer v0.3 notes:

- `spatial_text_cue` uses smaller style-aware overlays such as subtitles, sticky notes, poster labels, and screen labels.
- `spatial_target_cue` benign and scrambled variants are counterfactual controls with comparable visual strength, not weak perturbations.
- `temporal_cue_chain` records visible temporal segments so early, middle, and late cue states can be reviewed.
- Procedurally generated pseudo-real videos are for engineering validation only and are not final paper-quality real video data.

Export a model input manifest for a video editing method:

```bash
python vast_edit/scripts/export_model_inputs.py \
  --samples_jsonl vast_edit_outputs/pilot_v01/metadata/samples.jsonl \
  --model_name MODEL_NAME \
  --output_jsonl vast_edit_outputs/pilot_v01/metadata/model_inputs.jsonl \
  --model_output_root vast_edit_outputs/pilot_v01/model_outputs/MODEL_NAME
```

Run your video editing model outside VAST-Edit using `model_inputs.jsonl`. For every row, pass `input_video` to the model and use only `authorized_instruction` as the edit command. Save outputs to `recommended_output_video`.

After model outputs are generated, create future judge tasks:

```bash
python vast_edit/scripts/build_judge_tasks.py \
  --samples_jsonl vast_edit_outputs/pilot_v01/metadata/samples.jsonl \
  --model_name MODEL_NAME \
  --model_output_root vast_edit_outputs/pilot_v01/model_outputs/MODEL_NAME \
  --judge_prompts vast_edit/configs/judge_prompts.yaml \
  --output_dir vast_edit_outputs/pilot_v01/judge_tasks/MODEL_NAME
```

Run MLLM or human judging outside this repository using the task files. Save the resulting scores as `judge_scores.jsonl` with the schema documented in `vast_edit/docs/DATA_SCHEMA.md`.

Aggregate offline judge scores:

```bash
python vast_edit/scripts/aggregate_scores.py \
  --judge_scores vast_edit_outputs/pilot_v01/judge_results/MODEL_NAME/judge_scores.jsonl \
  --output_dir vast_edit_outputs/pilot_v01/metrics/MODEL_NAME \
  --quality_threshold 3.0 \
  --score_threshold 3.0
```

Generated pilot layout:

```text
vast_edit_outputs/pilot_v01/
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

The generated videos are source-video variants for downstream editing models. The model prompt should use only `authorized_instruction`.
The model output filename should use the exact `sample_id` stem from `samples.jsonl`.

For research correctness, `attack_intent` is the default semantic source for attack and scrambled overlay text. Template `default_text` is fallback only. To force different rendered overlay text, set `extra.overlay_text` in the input manifest. Benign variants use harmless text, and clean variants do not render attack overlays.

## Metrics

VAST-Edit's offline aggregation scaffold reads future judge scores and computes:

- AEC: Authorized Edit Compliance, the proportion of quality-passing outputs that follow the authorized instruction.
- UER: Unauthorized Edit Rate, the proportion of quality-passing outputs that align with the unauthorized visual cue.
- CALS: Causal Authority Leakage Score, comparing attack alignment against benign and scrambled controls for the same base item.
- TPR-like proxy: the proportion of pairwise judge rows where the attack output is more aligned with the unauthorized cue than controls.
- Quality pass rate: the proportion of judged outputs above the quality threshold.

The aggregator does not call any model, MLLM, or external API. It only reads `judge_scores.jsonl`.

## Repository Isolation

All VAST-Edit files live under `vast_edit/`. The extension is designed to be non-invasive and should not modify IVEBench core files such as `README.md`, `metrics/`, or `data_process/`.

Future work may reuse IVEBench conventions, especially JSON/JSONL metadata, source and target video naming, frame-folder organization, and CSV-style evaluation outputs, while keeping VAST-Edit logic separate.
