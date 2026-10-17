# CLAUDE.md

Experiment suite measuring how downscaling affects SynthID detection. See README.md for usage.

## Structure

Monorepo of independent apps under `apps/`, driven from the root `justfile`. Add a recipe there for anything new so nothing requires `cd`-ing into an app.

- `apps/prepare`: Go. Resampling methods live in `methods.go`; add new ones there.
- `apps/evals`: Python (uv). Checks run concurrently via `asyncio.gather` behind a semaphore against OpenAI's Content Provenance API, which only recognises OpenAI-generated images and is rate limited to roughly 20 checks an hour. The original is checked first and the run stops if SynthID is not confirmed there. LLMs cannot read SynthID, so do not use them as detectors.
- `apps/dashboard`: Python (uv). `results.py` holds all loading and analysis; `app.py` and `plot.py` only present it.

## Data contract

All generated data lives in `data/` (gitignored):

- `data/images/<name>/original.<ext>`: untouched source image, treated as scale 100.
- `data/images/<name>/<method>/<scale>.png`: scale is a zero-padded percentage.
- `data/results/<name>.jsonl`: append-only, one row per check with `image` (relative to `data/images/<name>`) and either `synthid` and `detail` or `error`. Reruns only check images without a verdict, and the last row per image wins.

Changing this layout means updating `prepare`, `evals` and `results.py` together.

## Conventions

- Keep code minimal; no comments that restate the code.
- Outputs are PNG so compression never confounds the resampling.
- Commit and push to `main` in small, focused commits. No branches.
- Never commit `.env` or anything in `data/`.
