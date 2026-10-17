import argparse
import asyncio
import json
import mimetypes
import time
from datetime import datetime
from pathlib import Path

import openai


class Checker:
    """Checks images for SynthID, caching verdicts in a JSONL file and waiting out rate limits."""

    def __init__(self, folder: Path, results: Path):
        self.folder = folder
        self.results = results
        self.client = openai.AsyncOpenAI(max_retries=0)
        self.verdicts = previous_verdicts(results)
        self.resume_at = 0.0

    async def detected(self, image: Path) -> bool:
        key = str(image.relative_to(self.folder))
        if key not in self.verdicts:
            row = {"image": key} | await self._check(image)
            self.verdicts[key] = row["synthid"]
            with self.results.open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(f"{key}: {row['synthid']}")
        return self.verdicts[key]

    async def _check(self, image: Path) -> dict:
        while True:
            while (delay := self.resume_at - time.time()) > 0:
                await asyncio.sleep(delay)
            try:
                result = await self.client.content_provenance_checks.create(
                    file=(image.name, image.read_bytes(), mimetypes.guess_type(image)[0])
                )
            except openai.RateLimitError as e:
                self.resume_at = max(self.resume_at, time.time() + float(e.response.headers.get("retry-after", 60)))
                print(f"rate limited, resuming at {datetime.fromtimestamp(self.resume_at):%H:%M:%S}")
                continue
            except (openai.APIConnectionError, openai.InternalServerError) as e:
                print(f"{e!r}, retrying in a minute")
                await asyncio.sleep(60)
                continue
            signals = {r.type: r for r in result.results}
            return {
                "synthid": signals["synthid"].outcome == "detected",
                "detail": ", ".join(f"{r.type}: {r.outcome}" + (f" ({r.model})" if r.model else "") for r in result.results),
            }


def previous_verdicts(results: Path) -> dict[str, bool]:
    if not results.exists():
        return {}
    rows = map(json.loads, results.read_text().splitlines())
    return {r["image"]: r["synthid"] for r in rows if "synthid" in r}


async def smallest_detected(checker: Checker, scales: list[Path]) -> int:
    """Binary search for the index of the smallest scale that still carries SynthID, assuming detection is monotonic."""
    lo, hi = 0, len(scales)
    while lo < hi:
        mid = (lo + hi) // 2
        if await checker.detected(scales[mid]):
            hi = mid
        else:
            lo = mid + 1
    return lo


async def evaluate(folder: Path, results: Path) -> None:
    original = next(folder.glob("original.*"), None)
    if original is None:
        raise SystemExit(f"no original image in {folder}")
    results.parent.mkdir(parents=True, exist_ok=True)
    checker = Checker(folder, results)

    if not await checker.detected(original):
        raise SystemExit(f"SynthID not detected in {original.name}, so there is nothing to search for")

    methods = {
        d.name: sorted(d.glob("*.png"), key=lambda p: int(p.stem)) for d in sorted(folder.iterdir()) if d.is_dir()
    }
    found = await asyncio.gather(*(smallest_detected(checker, scales) for scales in methods.values()))

    for (method, scales), i in zip(methods.items(), found):
        if i == 0:
            print(f"{method}: detected at every scale")
        elif i == len(scales):
            print(f"{method}: lost at every scale")
        else:
            print(f"{method}: detected down to {int(scales[i].stem)}%, lost at {int(scales[i - 1].stem)}%")


def main() -> None:
    parser = argparse.ArgumentParser(description="Find the scale at which each resampling method loses SynthID.")
    parser.add_argument("folder", type=Path, help="output of prepare")
    parser.add_argument("results", type=Path, help="JSONL file; images already checked in it are not checked again")
    args = parser.parse_args()
    try:
        asyncio.run(evaluate(args.folder, args.results))
    except openai.APIError as e:
        raise SystemExit(f"OpenAI API error: {e}")


if __name__ == "__main__":
    main()
