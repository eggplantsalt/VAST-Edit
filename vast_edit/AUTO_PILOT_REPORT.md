# VAST-Edit Auto Pilot v0.2 Report

## Summary

- Run result: successful.
- Source video strategy: pseudo-real generated videos.
- Reason: no suitable local real videos were found in the requested directories after excluding prior debug synthetic outputs.
- Source video directory: `/opt/data/private/zy_data/VAST-Edit/source_videos/auto_pilot_v02`
- Output directory: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02`
- These pseudo-real videos are engineering validation assets only. They are not final real-video data for a paper or benchmark release.

## Source Videos

| file | scene | path | fps | resolution | frames | duration_sec |
| --- | --- | --- | --- | --- | --- | --- |
| `auto_001.mp4` | desktop_scene | `/opt/data/private/zy_data/VAST-Edit/source_videos/auto_pilot_v02/auto_001.mp4` | 16.0 | 320x240 | 64 | 4.0 |
| `auto_002.mp4` | street_scene | `/opt/data/private/zy_data/VAST-Edit/source_videos/auto_pilot_v02/auto_002.mp4` | 16.0 | 320x240 | 64 | 4.0 |
| `auto_003.mp4` | kitchen_scene | `/opt/data/private/zy_data/VAST-Edit/source_videos/auto_pilot_v02/auto_003.mp4` | 16.0 | 320x240 | 64 | 4.0 |
| `auto_004.mp4` | garden_scene | `/opt/data/private/zy_data/VAST-Edit/source_videos/auto_pilot_v02/auto_004.mp4` | 16.0 | 320x240 | 64 | 4.0 |
| `auto_005.mp4` | workspace_scene | `/opt/data/private/zy_data/VAST-Edit/source_videos/auto_pilot_v02/auto_005.mp4` | 16.0 | 320x240 | 64 | 4.0 |

Probe metadata was also written to:

```text
/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/source_video_probe.json
```

## Manifest And Pilot Counts

- Base manifest: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/base_manifest.jsonl`
- Base manifest records: 10
- Expanded manifest: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/input_manifest.expanded.jsonl`
- Expanded manifest records: 30
- Generated samples manifest: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/pilot/metadata/samples.jsonl`
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

## Model Inputs And Judge Tasks

- Model inputs: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/pilot/metadata/model_inputs.pending_video_editor.jsonl`
- Judge task directory: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/judge_tasks/pending_video_editor`
- Single-video judge tasks: 120
- Pairwise judge tasks: 30

No video editing model was run. No MLLM API was called.

## Contact Sheets

- Overview contact sheet: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/debug_artifacts/contact_sheet_overview.png`
- Spatial text cue sheet: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/debug_artifacts/contact_sheet_spatial_text_cue.png`
- Spatial target cue sheet: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/debug_artifacts/contact_sheet_spatial_target_cue.png`
- Temporal cue chain sheet: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/debug_artifacts/contact_sheet_temporal_cue_chain.png`

## Fake Aggregation

- Fake judge scores: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/judge_results/pending_video_editor/judge_scores.fake.jsonl`
- Metrics directory: `/opt/data/private/zy_data/VAST-Edit/outputs/auto_pilot_v02/metrics/pending_video_editor`
- Aggregation result: successful.
- Outputs present: `summary.json`, `per_sample_scores.csv`, `per_group_cals.csv`
- `overall_mean_cals`: 2.8000000000000003
- Missing CALS groups: 0

## Code Changes

Code was modified only inside `vast_edit/`.

Files changed or added for this stage:

- `vast_edit/scripts/generate_pseudo_real_videos.py`: added reusable pseudo-real video generator for Auto Pilot v0.2.
- `vast_edit/AUTO_PILOT_REPORT.md`: this report.

Existing uncommitted files from the previous debug stage remain present:

- `vast_edit/requirements-minimal.txt`
- `vast_edit/scripts/make_contact_sheet.py`
- `vast_edit/scripts/validate_manifest.py`
- `vast_edit/scripts/inspect_manifest.py`
- `vast_edit/README.md`
- `vast_edit/docs/SERVER_RUNBOOK.md`
- `vast_edit/SERVER_DEBUG_REPORT.md`
- `vast_edit_outputs` symlink

## Limitations

The five source videos are procedurally generated pseudo-real scenes. They are useful for engineering validation of the VAST-Edit data path, overlay renderers, metadata contracts, contact sheets, judge task generation, and offline aggregation. They do not replace final curated real videos for research claims or paper-quality benchmark data.
