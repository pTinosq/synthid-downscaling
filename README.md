# synthid-downscaling

How far can an AI-generated image be downscaled, and with which resampling method, before SynthID stops being detected?

## Setup

Requires [Go](https://go.dev), [uv](https://docs.astral.sh/uv) and [just](https://just.systems).

```sh
cp .env.example .env   # add your OpenAI key (and OpenRouter key for LLM detectors)
```

## Usage

```sh
just prepare cat.png                       # data/images/cat/<method>/<scale>.png
just prepare cat.png -methods lanczos,box -min 5 -max 95 -step 5
just evals cat                             # data/results/cat/<timestamp>.jsonl
just evals cat --detectors openai-provenance,google/gemini-3.8-flash --concurrency 32
just dashboard                             # browse results and images
just plot data/results/cat/*.jsonl         # save charts next to each results file
```

Without `-methods`, `prepare` opens an interactive picker.

## Detectors

`openai-provenance` (the default) uses OpenAI's [Content Provenance API](https://developers.openai.com/api/docs/guides/content-provenance), which verifies SynthID watermarks and C2PA metadata. It only recognises OpenAI's signals, so source images must come from an OpenAI image model.

Any other detector name is treated as an OpenRouter model and simply asked whether it sees SynthID. LLMs cannot read the watermark, so treat these as a baseline for visual judgement, not detection.

## Layout

| Path | Purpose |
| --- | --- |
| `apps/prepare` | Go CLI that downscales an image with each resampling method at each scale |
| `apps/evals` | Python script that checks each image for SynthID with one or more detectors |
| `apps/dashboard` | Streamlit app and matplotlib script for analysing results |
| `data/` | Generated images and results (gitignored) |
