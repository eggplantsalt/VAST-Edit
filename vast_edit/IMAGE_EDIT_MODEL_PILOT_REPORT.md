# VAST-Edit Image-Edit Model Pilot v0.1 Report

## Summary

Image-Edit Model Pilot v0.1 was resumed and completed on the remote server.

- SSH orchestration: successful using the explicit key/host/port command.
- Remote repository: `/workspace/zy_workspace/VAST-Edit`.
- Remote data root: `/opt/data/private/zy_data/VAST-Edit`.
- Output root: `/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01`.
- Model: `timbrooks/instruct-pix2pix` through Diffusers `StableDiffusionInstructPix2PixPipeline`.
- Model cache: `/opt/data/private/zy_data/VAST-Edit/model_weights/hf_cache`.
- Smoke run: successful after resume.
- 24-input pilot: successful.
- Prompt policy: the model received only `authorized_instruction`; `attack_intent` was never passed to the image editing model.

## Recovery From Interrupted State

The previous run had stopped during the heavy dependency setup phase. The resumed run found:

- No active `pip`, `python`, or model-download processes.
- Existing environment: `/opt/data/private/zy_data/VAST-Edit/venvs/image-edit-pilot-v01`.
- Existing model cache root: `/opt/data/private/zy_data/VAST-Edit/model_weights/hf_cache`.

The existing `image-edit-pilot-v01` environment used Python 3.13.11. Installing current PyTorch there produced `torch 2.12.0+cu130`, but CUDA initialization failed because the server driver exposed CUDA 12.4 / NVIDIA driver 550.127.05 while that wheel requires a newer driver.

A Python 3.8 environment was therefore created at:

```text
/opt/data/private/zy_data/VAST-Edit/venvs/image-edit-pilot-v01-py38
```

This was necessary because the server only had system Python 3.8 and Python 3.13 available. An attempted Miniforge/Python 3.11 route failed because `github.com` could not be resolved from the server at that moment. The Python 3.8 environment uses a CUDA 12.1 compatible PyTorch wheel and successfully sees the GPU.

## Dependency And CUDA Status

Working environment:

```text
/opt/data/private/zy_data/VAST-Edit/venvs/image-edit-pilot-v01-py38
```

CUDA smoke test:

```json
{
  "torch_version": "2.4.1+cu121",
  "cuda_available": true,
  "cuda_version": "12.1",
  "device_count": 1,
  "device_name": "NVIDIA GeForce RTX 4090",
  "diffusers_version": "0.31.0",
  "transformers_version": "4.46.3",
  "accelerate_version": "1.0.1",
  "pil_version": "10.4.0",
  "cv2_version": "4.10.0",
  "numpy_version": "1.24.4",
  "cuda_tensor_sum": 4.0
}
```

The first Python 3.13 CUDA attempt failed with `torch.cuda.is_available() == false`; the final Python 3.8 CUDA 12.1 environment passed.

## Model Download

The selected model was:

```text
timbrooks/instruct-pix2pix
```

Initial direct Hugging Face access timed out. The run then used:

```text
HF_ENDPOINT=https://hf-mirror.com
HF_HOME=/opt/data/private/zy_data/VAST-Edit/model_weights/hf_cache
HF_HUB_CACHE=/opt/data/private/zy_data/VAST-Edit/model_weights/hf_cache
```

The model was downloaded/cached under:

```text
/opt/data/private/zy_data/VAST-Edit/model_weights/hf_cache/models--timbrooks--instruct-pix2pix
```

No model weights were written into the repository.

## Implemented Scripts

Added or updated:

- `vast_edit/scripts/extract_keyframes_for_editing.py`
- `vast_edit/scripts/run_image_edit_model_pilot.py`
- `vast_edit/scripts/analyze_image_edit_pilot.py`
- `vast_edit/IMAGE_EDIT_MODEL_PILOT_REPORT.md`

Script roles:

- `extract_keyframes_for_editing.py` selects a balanced 24-input subset and extracts one keyframe per rendered VAST-Edit source video.
- `run_image_edit_model_pilot.py` runs InstructPix2Pix on keyframes using only `authorized_instruction` as the prompt.
- `analyze_image_edit_pilot.py` computes lightweight pixel-change proxies and writes contact sheets for human inspection.

## Balanced 24-Input Subset

Source manifests:

```text
/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/pilot/metadata/samples.jsonl
/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/pilot/metadata/model_inputs.pending_video_editor.jsonl
```

Subset output:

```text
/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01/subset/model_inputs.image_edit_pilot_v01.jsonl
```

Selection:

- 2 source scenes: `desktop_scene_01`, `desktop_scene_02`.
- 3 attack families: `spatial_text_cue`, `spatial_target_cue`, `temporal_cue_chain`.
- 4 variants: `clean`, `benign`, `attack`, `scrambled`.
- Total: 24 inputs.

Distribution:

```text
clean=6
benign=6
attack=6
scrambled=6
spatial_text_cue=8
spatial_target_cue=8
temporal_cue_chain=8
```

Keyframes:

```text
/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01/keyframes
```

## Model Run

Runner command used the following core settings:

```text
model_id=timbrooks/instruct-pix2pix
model_name=instruct_pix2pix
resolution=256
num_inference_steps=8
seed=0
guidance_scale=7.5
image_guidance_scale=1.5
```

The 4-variant smoke initially wrote 3 successful rows and one interrupted `BrokenPipeError` row caused by local command interruption. The run was resumed, the fourth smoke sample succeeded, and the full 24-input pilot then completed.

Final deduplicated model results:

```text
total_records=24
ok=24
error=0
```

Model outputs:

```text
/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01/model_outputs/instruct_pix2pix
```

Raw result log:

```text
/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01/metadata/image_edit_results.instruct_pix2pix.jsonl
```

The raw result log has 25 rows because it preserves one interrupted smoke error row for auditability. The analysis script deduplicates by `sample_id` and reports 24 final records.

## Analysis Outputs

Analysis directory:

```text
/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01/analysis
```

Generated files:

- `summary.json`
- `per_sample.csv`
- `per_family.csv`
- `per_variant.csv`
- `contact_sheets/*.png`

Contact sheets:

```text
/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01/analysis/contact_sheets/desktop_scene_01__spatial_target_cue.png
/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01/analysis/contact_sheets/desktop_scene_01__spatial_text_cue.png
/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01/analysis/contact_sheets/desktop_scene_01__temporal_cue_chain.png
/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01/analysis/contact_sheets/desktop_scene_02__spatial_target_cue.png
/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01/analysis/contact_sheets/desktop_scene_02__spatial_text_cue.png
/opt/data/private/zy_data/VAST-Edit/outputs/image_edit_model_pilot_v01/analysis/contact_sheets/desktop_scene_02__temporal_cue_chain.png
```

## Quantitative Proxy Results

These are pixel-change proxies between the input keyframe and edited output image. They can detect variant-dependent sensitivity, but they do not prove semantic Visual Authority Confusion without a semantic judge.

Overall by variant:

| variant | records | mean_abs_diff | changed_pixel_rate_20 | changed_pixel_rate_40 |
| --- | ---: | ---: | ---: | ---: |
| attack | 6 | 69.99 | 0.986 | 0.945 |
| benign | 6 | 56.45 | 0.981 | 0.646 |
| clean | 6 | 50.25 | 0.970 | 0.484 |
| scrambled | 6 | 61.29 | 0.979 | 0.793 |

Attack deltas:

```text
attack_mean_abs_diff - benign_mean_abs_diff = +13.54
attack_mean_abs_diff - scrambled_mean_abs_diff = +8.70
```

By attack family and variant, mean absolute difference:

| attack_family | clean | benign | attack | scrambled |
| --- | ---: | ---: | ---: | ---: |
| spatial_text_cue | 39.21 | 65.95 | 78.72 | 62.91 |
| spatial_target_cue | 62.60 | 60.39 | 66.41 | 57.39 |
| temporal_cue_chain | 48.94 | 43.01 | 64.85 | 63.57 |

## Preliminary Interpretation

The pilot provides a real open-source image-editing signal: InstructPix2Pix generated outputs for all 24 VAST-Edit keyframes, and attack variants had the largest pixel-change proxy overall.

The strongest signal in this tiny pilot appears in `spatial_text_cue`, where attack variants produced substantially higher changes than clean, benign, and scrambled. This is the most promising early evidence for the Visual Authority Confusion framing: the model may be responding differently when semantically meaningful visual text is present, even though the textual prompt remains the authorized instruction.

`temporal_cue_chain` also shows attack above benign and clean, but scrambled is nearly as high as attack. That pattern may indicate that for a single extracted keyframe, temporal-chain overlays behave more like high-salience visual perturbations than semantic authority cues. Full video editing or multi-keyframe image editing would be needed before making a temporal claim.

`spatial_target_cue` shows only a small attack-control gap in this proxy. It may be better framed as Target Authority Hijacking when the model uses visual markers to choose an edit target, but this pilot's pixel proxy alone is not strong enough to confirm that.

A third framing, Pipeline Authority Laundering, remains relevant: if an upstream captioning/OCR/planning stage transcribes source-frame visual text and feeds it into an edit prompt, the authority leak becomes pipeline-mediated. This pilot did not use such a pipeline, so it is not direct evidence for laundering yet.

## Current Best Paper Narrative

The most promising narrative remains Visual Authority Confusion, with a sharper first empirical focus on text-like visual instructions in source frames. The benchmark should keep the counterfactual design:

- `clean`: original source.
- `benign`: similar visual obstruction without edit semantics.
- `scrambled`: similar visual texture with broken semantics.
- `attack`: unauthorized visual cue with edit semantics.

The first paper-quality study should combine model outputs with semantic human or MLLM judging, because pixel-change proxies cannot distinguish correct authorized edits from unauthorized visual-cue following.

## PROJECT_CONTEXT.md Update

`PROJECT_CONTEXT.md` was not updated in this run. The original framing is still viable, and the pilot results are preliminary rather than strong enough to justify changing project direction. The report records the possible sub-framings to revisit after semantic judging:

- Visual Authority Confusion.
- Target Authority Hijacking.
- Pipeline Authority Laundering.

## Limitations

- Source videos are still pseudo-real engineering validation videos from Auto Pilot v0.3, not final curated real videos.
- InstructPix2Pix is an image-editing proxy, not a full video-editing model.
- The pilot uses one keyframe per sample, so temporal cues are only partially tested.
- Analysis uses pixel-change proxies, not semantic MLLM or human judgments.
- The raw result log contains one preserved interrupted smoke error row, but final analysis deduplicates and reports 24 successful samples.

## Next Steps

1. Human-review the contact sheets to see whether attack variants produce qualitatively different edits.
2. Run the same 24 keyframes through a semantic judge prompt or human rubric.
3. Add a small semantic annotation file with fields similar to `authorized_edit_score`, `attack_alignment_score`, and `quality_score`.
4. Repeat on curated real videos rather than pseudo-real debug videos.
5. If temporal cues remain important, move from single keyframes to multiple keyframes or an actual video-editing model.
6. Consider a separate ablation for pipeline-mediated OCR/caption leakage.
## Git Commit And Push Status

The code/report changes were committed locally on the remote repository:

`	ext
commit=<see git rev-parse HEAD / final response>
message=Add image editing model pilot
`

Push failed because the remote uses an HTTPS URL that requires credentials in a non-interactive shell:

`	ext
fatal: could not read Username for 'https://gh.llkk.cc': No such device or address
`

The commit is preserved in the remote repository. No data-disk outputs, model weights, keyframes, edited images, or contact sheets were committed.
