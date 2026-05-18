# PROJECT_CONTEXT.md

## Project Name

VAST-Edit: A Causal Benchmark for Visual Authority Confusion in Instruction-Guided Video Editing

## Core Research Goal

We are building a benchmark for instruction-guided video editing models. The benchmark tests whether a model incorrectly treats visual content inside the source video as an authorized editing instruction.

The key safety problem is Visual Authority Confusion: in video editing, the user text instruction should be the authorized command, while the source video should be treated as editable content. If text, arrows, subtitles, UI boxes, trajectory marks, or other visual cues inside the source video affect the model’s editing behavior beyond the user instruction, the model has authority leakage.

Short slogan:

Video editing models should edit what is in the video, not obey what is written inside the video.

## Current Codebase Decision

We use IVEBench as the base codebase because it is an instruction-guided video editing benchmark with existing data organization, evaluation pipeline, and benchmark conventions.

We will not directly modify IVEBench core code unless necessary. We will add a separate extension directory:

IVEBench/
  vast_edit/

The goal is to keep the original repository clean and make our benchmark extension modular.

## Stage 0 Goal

Read the IVEBench repository, understand its structure, and create OVERVIEW.md.

No implementation yet.

## Stage 1 Goal

Implement a VAST-Edit data generation module under vast_edit/.

The module should generate four counterfactual versions for each source video and authorized editing instruction:

1. clean: original source video.
2. benign: source video with non-semantic visual overlay.
3. attack: source video with visual authority attack cue.
4. scrambled: source video with similar visual perturbation but semantically scrambled cue.

The first attack families are:

1. spatial_text_cue: scene text, subtitle-like text, poster text, sticky-note text.
2. spatial_target_cue: arrow, circle, box, highlight, target marker.
3. temporal_cue_chain: visual cues distributed across frames, such as fragmented text, progressive target binding, or motion trajectory cue.

## Core Metadata Schema

Each generated sample should have metadata fields similar to:

sample_id
source_video
authorized_instruction
attack_family
attack_intent
variant
overlay_params
expected_behavior
safety_rule
output_video
source_fps
source_num_frames
render_num_frames
render_resolution

## Expected Directory Design

Proposed extension structure:

vast_edit/
  README.md
  configs/
    attack_templates.yaml
    pilot_v01.yaml
  data/
    input_manifest_examples/
    generated/
  vast_edit/
    __init__.py
    io/
    overlays/
    templates/
    renderers/
    metadata/
    utils/
  scripts/
    build_pilot.py
    inspect_manifest.py
  docs/
    DATA_SCHEMA.md
    ATTACK_TAXONOMY.md

This structure may be adjusted after reading IVEBench, but the extension should remain isolated.

## Engineering Constraints

The user works with a local code agent but runs experiments on a remote headless server. Local machine may not have the Python environment, GPU, or model dependencies.

Therefore:

- Do not run GPU inference locally.
- Do not download large datasets or model weights locally.
- Do not rely on GUI.
- Avoid heavy tests.
- Prefer writing code that can be checked syntactically and reviewed manually.
- Use simple dependencies where possible: Python standard library, OpenCV, PIL, numpy, yaml, tqdm.
- Keep changes modular and reversible.
- Do not modify original IVEBench files unless explicitly requested.

## Research Metrics Planned Later

The benchmark will later evaluate:

AEC: Authorized Edit Compliance.
UER: Unauthorized Edit Rate.
CALS: Causal Authority Leakage Score.
TPR: Temporal Persistence Rate.
Quality Gate: whether output video remains valid enough to evaluate.

But Stage 1 only builds input videos and metadata. Model inference and evaluation will be added later.

## Important Design Principle

Do not over-engineer. Implement the minimal robust version first.

The first deliverable is a working VAST-Edit v0.1 pilot data generator, not the full final benchmark.

## Interaction Rule for Code Agent

When asked to implement, make concrete file edits.

When asked to inspect, do not modify source files except explicitly requested output files such as OVERVIEW.md.

Before changing any original IVEBench code, explain why it is necessary and ask for confirmation.
## Real-Video Benchmark Track Update (2026-05-19)

Pseudo-real videos remain useful engineering smoke-test assets, but they are not sufficient for paper-grade benchmark evidence. Starting with Real Video Pilot v0.1, VAST-Edit should treat curated real public/research videos as the main benchmark track, with pseudo-real assets kept only for fast renderer and pipeline debugging.

The first real-video source plan is a small DAVIS 2017 / 2016 style subset because DAVIS provides public research video sequences with real objects, camera motion, and scene texture. Each real-video source must have a license/attribution manifest. Future claims should distinguish:

- engineering validation on pseudo-real generated videos;
- benchmark evidence on curated real videos;
- semantic model behavior evidence from human or MLLM judging, not pixel-change proxies alone.