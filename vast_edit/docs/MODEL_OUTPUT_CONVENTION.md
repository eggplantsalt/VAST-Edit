# Model Output Convention

VAST-Edit evaluates whether a video editing model follows the authorized instruction and ignores unauthorized visual cues in the source video. To support reliable aggregation, model outputs must follow a stable naming and directory convention.

## Input Identity

Each rendered VAST-Edit source variant has:

- `sample_id`: unique variant-level ID from `metadata/samples.jsonl`;
- `base_id`: source instruction ID;
- `variant`: one of `clean`, `benign`, `attack`, `scrambled`;
- `attack_family`: visual cue family;
- `authorized_instruction`: the only command the model should follow.

The `sample_id` must remain unchanged through model inference and judging.

## Required Output Layout

For a pilot output directory such as `output/`, model-generated edited videos should be organized as:

```text
output/
  model_outputs/
    MODEL_NAME/
      clean/
        sample_id.mp4
      benign/
        sample_id.mp4
      attack/
        sample_id.mp4
      scrambled/
        sample_id.mp4
```

For example:

```text
output/model_outputs/anyv2v/attack/vast_demo_001_spatial_text_cue_attack_ab12cd34ef.mp4
```

The filename stem must exactly match `sample_id` from `samples.jsonl`.

## Model Input Manifest

Use `vast_edit/scripts/export_model_inputs.py` to create `model_inputs.jsonl`:

```bash
python vast_edit/scripts/export_model_inputs.py \
  --samples_jsonl output/metadata/samples.jsonl \
  --model_name MODEL_NAME \
  --output_jsonl output/metadata/model_inputs.jsonl \
  --model_output_root output/model_outputs/MODEL_NAME
```

Each row contains:

| Field | Description |
| --- | --- |
| `sample_id` | Must match VAST-Edit `samples.jsonl`. |
| `base_id` | Source instruction ID. |
| `variant` | `clean`, `benign`, `attack`, or `scrambled`. |
| `attack_family` | VAST-Edit attack family. |
| `input_video` | Rendered VAST-Edit source variant to pass to the model. |
| `authorized_instruction` | The only edit instruction to pass to the model. |
| `target_prompt` | Expected target description under the authorized instruction. |
| `expected_behavior` | Robust-model behavior expectation. |
| `safety_rule` | Authority rule for this sample. |
| `recommended_output_video` | Conventional destination for the model output. |
| `notes` | Reminder about authority boundaries. |

## Authority Rule

The model input instruction must be `authorized_instruction`. Visual text, UI, arrows, subtitles, target markers, highlights, trajectory cues, or labels inside the video must not be extracted, appended to the prompt, or treated as user commands.

## Judge Task Inputs

After model outputs are created, `vast_edit/scripts/build_judge_tasks.py` can generate future judge task files:

```bash
python vast_edit/scripts/build_judge_tasks.py \
  --samples_jsonl output/metadata/samples.jsonl \
  --model_name MODEL_NAME \
  --model_output_root output/model_outputs/MODEL_NAME \
  --judge_prompts vast_edit/configs/judge_prompts.yaml \
  --output_dir output/judge_tasks/MODEL_NAME
```

This creates:

```text
output/judge_tasks/MODEL_NAME/
  judge_tasks.single.jsonl
  judge_tasks.pairwise.jsonl
```

These are task definitions only; they do not call any MLLM or human labeling service.
