# synthid-downscaling

This repo measures how much you can downscale an AI-generated image before SynthID detection fails. It compares different resampling methods and scales.

## Install

1. Install [Go](https://go.dev), [uv](https://docs.astral.sh/uv) and [just](https://just.systems):

   ```sh
   brew install go uv just
   ```

2. Copy the example environment file:

   ```sh
   cp .env.example .env
   ```

3. Add your `OPENAI_API_KEY` to `.env`.

Run all commands from the repo root. Dependencies install automatically on the first run.

## Use

1. Generate downscaled versions of an image:

   ```sh
   just prepare cat.png
   ```

   An interactive picker asks for the resampling methods. The images go to `data/images/cat/`.

2. Check each image for SynthID:

   ```sh
   just evals cat
   ```

   The results go to `data/results/cat/<timestamp>.jsonl`.

3. Look at the results in the dashboard:

   ```sh
   just dashboard
   ```

To save the charts as PNG files instead, run `just plot data/results/cat/*.jsonl`.

## Options

| Command | Example |
| --- | --- |
| Set methods without the picker | `just prepare cat.png -methods lanczos,box` |
| Set the scale range in percent | `just prepare cat.png -min 5 -max 95 -step 5` |
| Send more requests at the same time | `just evals cat --concurrency 32` |

Run `just` to see all commands.

## Detection

`just evals` uses OpenAI's [Content Provenance API](https://developers.openai.com/api/docs/guides/content-provenance) to verify the SynthID watermark. This API only finds OpenAI watermarks, so use images from an OpenAI image model.

## Layout

| Path | Contents |
| --- | --- |
| `apps/prepare` | Go CLI that downscales images |
| `apps/evals` | Python script that checks images for SynthID |
| `apps/dashboard` | Streamlit dashboard and chart script |
| `data/` | Generated images and results (not in git) |
