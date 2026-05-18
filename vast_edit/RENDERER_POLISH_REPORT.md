# VAST-Edit Renderer Polish v0.3 Report

## Initial Plan

Auto Pilot v0.2 completed the engineering path but exposed overlay-quality issues in contact sheets. The v0.3 polish plan is:

1. Make `spatial_text_cue` look more like in-scene subtitles, sticky notes, labels, or screen UI rather than a large high-contrast warning banner.
2. Make `spatial_target_cue` counterfactual controls visually fair: benign and scrambled should retain similar salience, line width, color, area, and duration while breaking target semantics.
3. Make `temporal_cue_chain` visible across multiple frame ranges and record those ranges in resolved overlay metadata for audit and contact-sheet selection.
4. Make `make_contact_sheet.py` produce the original overview plus a temporal multi-frame sheet using metadata-selected early/middle/late frames.
5. Re-run the full 5-video, 10-base-record, 30-expanded-record, 120-sample auto pilot into `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03`.

## Results

Successful.

## Renderer Changes

Modified renderers:

- `vast_edit/vast_edit/overlays/base.py`
- `vast_edit/vast_edit/overlays/spatial_text.py`
- `vast_edit/vast_edit/overlays/spatial_target.py`
- `vast_edit/vast_edit/overlays/temporal_chain.py`
- `vast_edit/vast_edit/builder.py`
- `vast_edit/configs/attack_templates.yaml`

### spatial_text_cue

`spatial_text_cue` now supports style-aware text overlays:

- `subtitle`
- `sticky_note`
- `poster_label`
- `screen_label`

The renderer no longer defaults to a large high-contrast black/yellow block. It uses resolution-aware font scale, max width, padding, opacity, border, and placement defaults. On 320x240 source videos, text is kept compact enough for model-pilot use and human review. Attack text still defaults to `attack_intent`, benign text remains semantically harmless, and scrambled text preserves visual texture while breaking instruction semantics.

Resolved `overlay_params` now include:

- `text_style`
- `font_scale`
- `placement_policy`
- `visible_frame_ranges`

### spatial_target_cue

`spatial_target_cue` now treats benign and scrambled as visually fair counterfactual controls:

- Benign keeps comparable marker size, color, line width, opacity, and duration, but moves the marker to a decorative neutral region or otherwise removes target binding.
- Scrambled keeps visual strength but randomizes marker location, direction, or binding.
- Attack continues to mark a clear unauthorized region when no object-level geometry is available.

Resolved `overlay_params` now include:

- `target_policy`
- `counterfactual_policy`
- `visible_frame_ranges`

### temporal_cue_chain

`temporal_cue_chain` now records visible temporal ranges and makes cue evolution easier to audit:

- `fragmented_text` uses multiple visible text segments.
- `progressive_target_binding` shows a marker first and a text cue later.
- `motion_trajectory` grows over successive frame segments and marks the current trajectory point.
- Benign and scrambled variants retain comparable temporal salience while neutralizing or breaking semantics.

Resolved `overlay_params` now include:

- `temporal_segments`
- `visible_frame_ranges`
- `temporal_policy`

## Contact Sheets

`vast_edit/scripts/make_contact_sheet.py` still writes the original overview and per-family sheets, but now selects visible frames from renderer metadata when possible. It also writes a temporal multi-frame sheet:

- `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/debug_artifacts/contact_sheet_overview.png`
- `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/debug_artifacts/contact_sheet_spatial_text_cue.png`
- `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/debug_artifacts/contact_sheet_spatial_target_cue.png`
- `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/debug_artifacts/contact_sheet_temporal_cue_chain.png`
- `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/debug_artifacts/contact_sheet_temporal_cue_chain_multiframe.png`

The multi-frame temporal sheet shows early, middle, and late cue states for each `clean` / `benign` / `attack` / `scrambled` temporal variant.

## Auto Pilot v0.3 Run

- Source videos: reused the five pseudo-real source videos from Auto Pilot v0.2.
- Output directory: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03`
- Base records: 10
- Expanded records: 30
- Generated samples: 120

Variant distribution:

```text
clean=30
benign=30
attack=30
scrambled=30
```

Attack family distribution:

```text
spatial_text_cue=40
spatial_target_cue=40
temporal_cue_chain=40
```

Generated files:

- Samples: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/pilot/metadata/samples.jsonl`
- Model inputs: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/pilot/metadata/model_inputs.pending_video_editor.jsonl`
- Judge tasks: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/judge_tasks/pending_video_editor`
- Fake judge scores: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/judge_results/pending_video_editor/judge_scores.fake.jsonl`
- Metrics: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v03/metrics/pending_video_editor`

Fake aggregation:

- Result: successful.
- Outputs present: `summary.json`, `per_sample_scores.csv`, `per_group_cals.csv`.
- `overall_mean_cals`: 2.7
- Missing CALS groups: 0

## Limitations

The v0.3 source videos are still procedurally generated pseudo-real scenes. They are useful for engineering validation and for preparing a controlled model pilot, but they are not final paper-quality real video data. The target geometry is still heuristic rather than object-detection-based, so visual target binding is region-based unless future manifests provide object boxes.

## Next Step

The engineering path is ready for Model Pilot v0.1. Recommended next step: run a small video editing method on the `model_inputs.pending_video_editor.jsonl` manifest while preserving the rule that only `authorized_instruction` is passed as the edit command.
