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
   just prepare gemini_dog.jpeg
   ```

   An interactive picker asks for the resampling methods. The images go to `data/images/gemini_dog/`.

2. Check each image for SynthID:

   ```sh
   just evals gemini_dog
   ```

   The results go to `data/results/gemini_dog.jsonl`. The original image is checked first. If SynthID is not found in the original, the run stops.

   The API allows approximately 20 checks per hour. If some checks fail, run the same command again later. It only checks the images that do not have a result.

3. Look at the results in the dashboard:

   ```sh
   just dashboard
   ```

To save the chart as a PNG file instead, run `just plot gemini_dog`.

## Options

| Command | Example |
| --- | --- |
| Set methods without the picker | `just prepare gemini_dog.jpeg -methods lanczos,box` |
| Set the scale range in percent | `just prepare gemini_dog.jpeg -min 5 -max 95 -step 5` |
| Send more requests at the same time | `just evals gemini_dog --concurrency 32` |

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
