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
   just prepare examples/openai_dog.png
   ```

   An interactive picker asks for the resampling methods. The tool makes one image for each method at each scale from 1% to 99%. The images go to `data/images/openai_dog/`.

2. Find the scale at which each method loses SynthID:

   ```sh
   caffeinate -i just evals openai_dog
   ```

   This can run for hours, so leave it on overnight. `caffeinate -i` stops your Mac from sleeping during the run.

   The script checks the original image first. If SynthID is not found in the original, it stops. Then it does a binary search over the scales of each method, so it only checks approximately 7 images per method. When the API rate limit is reached, the script waits and continues.

   The results go to `data/results/openai_dog.jsonl`. If you stop the script, run the same command again. It continues from where it stopped.

3. Look at the results in the dashboard:

   ```sh
   just dashboard
   ```

To save the chart as a PNG file instead, run `just plot openai_dog`.

## Options

| Command | Example |
| --- | --- |
| Set methods without the picker | `just prepare examples/openai_dog.png -methods lanczos,box` |
| Set the scale range in percent | `just prepare examples/openai_dog.png -min 5 -max 95 -step 5` |

Run `just` to see all commands.

## Detection

`just evals` uses OpenAI's [Content Provenance API](https://developers.openai.com/api/docs/guides/content-provenance) to verify the SynthID watermark. This API only finds OpenAI watermarks, so use images from an OpenAI image model.

The binary search assumes that when a method loses SynthID at one scale, it also loses it at all smaller scales.

## Layout

| Path | Contents |
| --- | --- |
| `apps/prepare` | Go CLI that downscales images |
| `apps/evals` | Python script that checks images for SynthID |
| `apps/dashboard` | Streamlit dashboard and chart script |
| `data/` | Generated images and results (not in git) |
