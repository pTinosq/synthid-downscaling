# CLAUDE.md

Experiment suite measuring how downscaling affects SynthID detection. See README.md for usage.

## Structure

Monorepo of independent apps under `apps/`, driven from the root `justfile`. Add a recipe there for anything new so nothing requires `cd`-ing into an app.

- `apps/prepare`: Go. Resampling methods live in `methods.go`; add new ones there.
- `apps/evals`: Python (uv). Detectors run concurrently via `asyncio.gather` behind a semaphore. `openai-provenance` is the real SynthID check and only recognises OpenAI-generated images; other detector names are OpenRouter models, which cannot actually read watermarks.
- `apps/dashboard`: Python (uv). `results.py` holds all loading and analysis; `app.py` and `plot.py` only present it.

## Data contract

All generated data lives in `data/` (gitignored):

- `data/images/<name>/original.<ext>`: untouched source image, treated as scale 100.
- `data/images/<name>/<method>/<scale>.png`: scale is a zero-padded percentage.
- `data/results/<name>/<timestamp>.jsonl`: one row per image and detector with `image` (relative to `data/images/<name>`), `detector`, and either `synthid` and `detail` or `error`.

Changing this layout means updating `prepare`, `evals` and `results.py` together.

## Conventions

- Keep code minimal; no comments that restate the code.
- Outputs are PNG so compression never confounds the resampling.
- Commit and push to `main` in small, focused commits. No branches.
- Never commit `.env` or anything in `data/`.
