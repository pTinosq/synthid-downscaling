import argparse
import asyncio
import json
import mimetypes
from pathlib import Path

from openai import AsyncOpenAI

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


async def check(client: AsyncOpenAI, image: Path) -> dict:
    result = await client.content_provenance_checks.create(
        file=(image.name, image.read_bytes(), mimetypes.guess_type(image)[0])
    )
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


async def evaluate(folder: Path, results: Path, concurrency: int) -> None:
    images = sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES)
    original = next((p for p in images if p.parent == folder and p.stem == "original"), None)
    verdicts = previous_verdicts(results)
    pending = [p for p in images if str(p.relative_to(folder)) not in verdicts]

    client = AsyncOpenAI(max_retries=5)
    limit = asyncio.Semaphore(concurrency)
    results.parent.mkdir(parents=True, exist_ok=True)

    with results.open("a") as f:

        async def run(image: Path) -> None:
            row = {"image": str(image.relative_to(folder))}
            async with limit:
                try:
                    row |= await check(client, image)
                    verdicts[row["image"]] = row["synthid"]
                except Exception as e:
                    row["error"] = repr(e)
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(f"{row['image']}: {row.get('synthid', 'error')}")

        if original in pending:
            pending.remove(original)
            await run(original)
        if original and not verdicts.get(original.name):
            raise SystemExit(f"SynthID not confirmed in {original.name}, so the downscaled images were skipped")

        await asyncio.gather(*map(run, pending))

    missing = len(images) - len(verdicts)
    print(f"{len(verdicts)} of {len(images)} images checked" + (f", run again to retry {missing}" if missing else ""))


def main() -> None:
    parser = argparse.ArgumentParser(description="Check every image in a folder for SynthID.")
    parser.add_argument("folder", type=Path)
    parser.add_argument("results", type=Path, help="JSONL file; images already checked in it are skipped")
    parser.add_argument("--concurrency", type=int, default=16, help="max requests in flight")
    args = parser.parse_args()
    asyncio.run(evaluate(args.folder, args.results, args.concurrency))


if __name__ == "__main__":
    main()
