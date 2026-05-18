# IVEBench Repository Overview

## Repository Summary

IVEBench is a benchmark and evaluation toolkit for instruction-guided video editing. The repository does not contain model inference code for generating edited videos; it assumes a user has already run a video editing model on the IVEBench database and produced target videos. The code here mainly supports:

- preparing video data as frame folders;
- loading benchmark metadata from a JSON file;
- running quality, instruction-compliance, and fidelity metrics;
- exporting per-video metric scores to CSV;
- aggregating per-video scores into a method-level summary.

The benchmark evaluates edited videos against source videos and prompt metadata. Metrics are split into three dimensions:

- video quality: subject consistency, temporal flickering, background consistency, motion smoothness, VTSS;
- instruction compliance: overall semantic consistency, instruction satisfaction, phrase semantic consistency, quantity accuracy;
- video fidelity: semantic fidelity, motion fidelity, content fidelity.

## Top-Level Directory Tree

Ignored here: `.git`, cache folders, weights/checkpoints, large data/video/result folders.

```text
IVEBench/
  assets/
    data_fig1.png
    pipeline.png
    performance_table.png
    qualitative_analysis.png
    qualitative_analysis_appendix.png
    radar_chart.png
    teaser.png
    title.png
  data_process/
    mp42frames_batch.py
    resize_batch.py
  docs/
  metrics/
    compliance/
      groundingdino/
      qwen_vl_utils/
      videoclipxl_utils/
      instruction_satisfaction.py
      overall_semantic_consistency.py
      phrase_semantic_consistency.py
      quantity_accuracy.py
    fidelity/
      cotracker/
      qwen_vl_utils/
      videoclipxl_utils/
      content_fidelity.py
      motion_fidelity.py
      semantic_fidelity.py
    quality/
      amt/
      training_suitability_assessment/
      background_consistency.py
      motion_smoothness.py
      subject_consistency.py
      temporal_flickering.py
      vtss.py
    evaluate.py
    get_average_score.py
    ivebench.py
    ivebench_utils.py
    path.yml
  ivebench.yml
  README.md
  requirements.txt
```

## Key Directories

- `metrics/`: main benchmark implementation. It contains the CLI entrypoint, metric dispatcher, metadata/frame loading helpers, metric implementations, and model path config.
- `metrics/quality/`: target-video quality metrics. Some metrics load CLIP/DINO/AMT/VTSS-related models.
- `metrics/compliance/`: instruction-compliance metrics. Includes Qwen2.5-VL MLLM judging, VideoCLIP-XL text-video similarity, and GroundingDINO quantity checks.
- `metrics/fidelity/`: source-target fidelity metrics. Includes Qwen2.5-VL content judging, VideoCLIP-XL video similarity, and CoTracker motion similarity.
- `data_process/`: utility scripts for converting `.mp4` videos to frame folders and resizing/sampling frame folders.
- `assets/`: README/website figures only.
- `docs/`: currently empty in this checkout.

## Data Format

The README says each source video has associated source prompt, edit prompt, target prompt, target phrase, and target span in a JSON file from the IVEBench database. The code path that actually loads metadata is `metrics/ivebench_utils.py::load_video_info`.

Required fields used by current metrics:

```json
[
  {
    "id": 0,
    "src_video_name": "example.mp4",
    "category": "style_editing",
    "subcategory": "example subtype",
    "source_prompt": "description of the original video",
    "edit_prompt": "instruction for editing",
    "target_prompt": "description of expected edited video"
  }
]
```

Fields mentioned in README but not preserved by `load_video_info`:

- `target_phrase`
- `target_span`

Important path convention:

- `src_video_name` includes the original video filename, typically with `.mp4`.
- Frame folders are addressed by stripping the extension: `os.path.splitext(src_video_name)[0]`.
- Source frame folder: `<source_videos_path>/<video_stem>/`.
- Target frame folder: `<target_videos_path>/<video_stem>/`.
- Target video filenames or folder names must match source video names/stems.
- Frame files are expected to be sortable image names such as `%05d.png`; several loaders accept `.png`, `.jpg`, `.jpeg`, and sometimes more image extensions.

Prompt usage by metric:

- `edit_prompt`: used by `instruction_satisfaction`, `content_fidelity`, `phrase_semantic_consistency`, and `quantity_accuracy`.
- `target_prompt`: used by `overall_semantic_consistency`.
- `source_prompt`: loaded but not visibly used by the inspected metric implementations.
- `category` / `subcategory`: used for result grouping and skip logic, e.g. quantity tasks and motion-fidelity exclusions.

## Evaluation Pipeline

1. Convert source and generated target `.mp4` videos to frame folders:

   ```bash
   python data_process/mp42frames_batch.py --input_path INPUT_MP4_DIR --output_path OUTPUT_FRAME_DIR
   ```

2. Optionally resize and uniformly sample frame folders:

   ```bash
   python data_process/resize_batch.py --input_path INPUT_FRAMES --output_path OUTPUT_FRAMES --size WIDTH HEIGHT --max_frame MAX_FRAME
   ```

3. Run per-video metrics from inside `metrics/`:

   ```bash
   python evaluate.py \
     --output_path OUTPUT_DIR \
     --source_videos_path SOURCE_FRAME_DIR \
     --target_videos_path TARGET_FRAME_DIR \
     --info_json_path PROMPT_JSON_PATH \
     --metric metric_1 metric_2
   ```

4. `metrics/evaluate.py` parses CLI args, selects `cuda` if available, constructs `VEBench`, and calls `VEBench.evaluate(...)`.

5. `metrics/ivebench.py::VEBench.evaluate` validates paths, builds or accepts a metric list, prioritizes `content_fidelity` and `instruction_satisfaction`, then dynamically imports metric modules:

   ```text
   quality.<metric>
   compliance.<metric>
   fidelity.<metric>
   ```

   Each metric module must expose a function named `compute_<metric>()`.

6. Each metric calls `load_video_info(json_dir, metric)` from `metrics/ivebench_utils.py`, resolves frame/video paths using `src_video_name`, computes per-video scores, and returns:

   ```python
   (average_score, detailed_video_results)
   ```

7. `VEBench.save_results_to_csv` merges all metric result lists by `video_name` or `video_id`, writes one CSV row per video, and creates columns like `<metric>_score`.

8. `metrics/get_average_score.py` is intended to aggregate the per-video CSV into dimension and total scores with configurable dimension weights.

## MLLM-Based Evaluation

MLLM-based evaluation is implemented as metric modules, not as a separate top-level MLLM-only script.

- `metrics/compliance/instruction_satisfaction.py`: loads Qwen2.5-VL and asks it to rate whether the edited target matches the source video after applying `edit_prompt`.
- `metrics/fidelity/content_fidelity.py`: loads Qwen2.5-VL and asks it to rate whether the target preserves source content outside the requested edit.

Both modules temporarily convert frame folders into compressed videos with ffmpeg before sending source and target videos to Qwen2.5-VL.

## Traditional / Non-MLLM Metrics

Traditional and model-based non-MLLM metrics are implemented as independent metric modules under `metrics/quality`, `metrics/compliance`, and `metrics/fidelity`, but they are invoked through the shared `metrics/evaluate.py` / `VEBench` dispatcher.

Examples:

- `temporal_flickering.py`: frame-to-frame MAE-derived score.
- `background_consistency.py`: CLIP image feature consistency across target frames.
- `subject_consistency.py`: DINO feature consistency across target frames.
- `motion_smoothness.py`: AMT frame interpolation based score.
- `vtss.py`: training suitability model score.
- `overall_semantic_consistency.py`: VideoCLIP-XL target video vs. `target_prompt`.
- `phrase_semantic_consistency.py`: VideoCLIP-XL target video vs. `edit_prompt`.
- `quantity_accuracy.py`: GroundingDINO object-count check for quantity modification tasks.
- `semantic_fidelity.py`: VideoCLIP-XL source-target video similarity.
- `motion_fidelity.py`: CoTracker source-target trajectory similarity.

## Config, Loader, and CLI Entrypoints

- CLI entrypoints:
  - `metrics/evaluate.py`
  - `metrics/get_average_score.py`
  - `data_process/mp42frames_batch.py`
  - `data_process/resize_batch.py`
- Metadata loader:
  - `metrics/ivebench_utils.py::load_video_info`
- Frame/video helpers:
  - `metrics/ivebench_utils.py`
  - per-metric helper classes and functions
- Metric path config:
  - `metrics/path.yml`
- Environment files:
  - `requirements.txt`
  - `ivebench.yml`

There is no general dataset class for IVEBench itself. Metric modules directly load the JSON metadata and read frame folders from paths passed via CLI.

## Important Files To Inspect Next

- `metrics/ivebench.py`
- `metrics/ivebench_utils.py`
- `metrics/evaluate.py`
- `metrics/get_average_score.py`
- `metrics/path.yml`
- `metrics/compliance/instruction_satisfaction.py`
- `metrics/fidelity/content_fidelity.py`
- `metrics/compliance/overall_semantic_consistency.py`
- `metrics/compliance/phrase_semantic_consistency.py`
- `metrics/compliance/quantity_accuracy.py`
- `metrics/fidelity/semantic_fidelity.py`
- `metrics/fidelity/motion_fidelity.py`
- `data_process/mp42frames_batch.py`
- `data_process/resize_batch.py`

## Extension Plan

To add VAST-Edit without disrupting IVEBench, prefer a separate top-level directory:

```text
vast_edit/
  README.md
  configs/
  data/
  eval/
  metrics/
  scripts/
```

Non-invasive approach:

- Do not edit existing IVEBench metric modules initially.
- Reuse IVEBench conventions where useful: JSON metadata, `src_video_name`, frame-folder stems, source/target path separation, CSV output.
- Add a VAST-Edit-specific metadata schema that extends rather than replaces IVEBench fields. For Visual Authority Confusion, likely extra fields include source visual distractor type, visible text/UI/arrow content, authorized user instruction, forbidden visual pseudo-instruction, expected edit behavior, and evaluation labels.
- Implement VAST-Edit evaluation as separate scripts under `vast_edit/`, with adapters that can optionally call IVEBench frame helpers or metrics.
- If reuse from `metrics/` is needed, import read-only helpers such as frame loading patterns, but avoid changing global dispatcher behavior until the VAST-Edit API is stable.
- Keep VAST-Edit outputs separate, e.g. `vast_edit/outputs/` or user-specified output directories, so original IVEBench results are untouched.
- If later integration is desired, add a thin optional bridge rather than modifying the default IVEBench metric list.

Suggested VAST-Edit metadata direction:

```json
{
  "id": "vast_edit_000001",
  "src_video_name": "example.mp4",
  "source_prompt": "description of source video",
  "authorized_edit_prompt": "actual user instruction",
  "visual_distractor_text": "text/arrow/UI/subtitle visible inside the video",
  "visual_distractor_type": "subtitle|ui|arrow|label|trajectory|watermark|other",
  "target_prompt": "expected edited video if only authorized instruction is followed",
  "should_ignore_visual_instruction": true,
  "expected_failure_mode": "model follows visual distractor instead of user prompt"
}
```

## Risks / Unknowns

- The actual IVEBench database JSON was not present locally, so the exact full schema is inferred from README and loader code.
- README mentions `target_phrase` and `target_span`, but `metrics/ivebench_utils.py::load_video_info` drops those fields. It is unclear whether any intended metric originally used them.
- `metrics/get_average_score.py` appears to have a bug: `parse_args()` returns only input and output paths, while `main()` expects five values including dimension weights.
- `metrics/ivebench.py::evaluate` accepts `save_json_results=True` but does not call `save_results_to_json`.
- Several metrics assume the current working directory is `metrics/` because default `path.yml` and relative model paths are resolved from there.
- Some modules contain mojibake/encoding artifacts in comments or regex strings.
- `ivebench_utils.py` references `logger` in helper exception branches without defining a module logger.
- Some metrics use `torch.hub` or model-loading fallbacks that may trigger network access if checkpoints are absent.
- MLLM scoring prompt templates are embedded directly in metric scripts, so changing MLLM behavior currently requires code edits.
- There is no unified config parser for benchmark data or metric runs beyond argparse and `metrics/path.yml`.
