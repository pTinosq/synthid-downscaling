import argparse
import asyncio
import json
import mimetypes
from datetime import datetime
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


async def evaluate(folder: Path, concurrency: int, out: Path) -> None:
    images = sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES)
    if not images:
        raise SystemExit(f"no images found in {folder}")

    client = AsyncOpenAI(max_retries=5)
    limit = asyncio.Semaphore(concurrency)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w") as f:

        async def run(image: Path) -> None:
            row = {"image": str(image.relative_to(folder))}
            async with limit:
                try:
                    row |= await check(client, image)
                except Exception as e:
                    row["error"] = repr(e)
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(f"{row['image']}: {row.get('synthid', 'error')}")

        await asyncio.gather(*map(run, images))

    print(f"wrote {len(images)} results to {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check every image in a folder for SynthID.")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--concurrency", type=int, default=16, help="max requests in flight")
    parser.add_argument("--out", type=Path, help="results file (default: results/<timestamp>.jsonl)")
    args = parser.parse_args()

    out = args.out or Path("results") / f"{datetime.now():%Y%m%d-%H%M%S}.jsonl"
    asyncio.run(evaluate(args.folder, args.concurrency, out))


if __name__ == "__main__":
    main()
