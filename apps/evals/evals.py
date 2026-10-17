import argparse
import asyncio
import base64
import json
import mimetypes
import os
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path

from openai import AsyncOpenAI
from pydantic import BaseModel

PROVENANCE = "openai-provenance"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_RETRIES = 5
PROMPT = (
    "Check this image for a SynthID watermark. "
    "Answer synthid=true only if you detect SynthID, and briefly explain your reasoning in the detail field."
)


class Verdict(BaseModel):
    synthid: bool
    detail: str


Detector = Callable[[Path], Awaitable[Verdict]]


async def check_provenance(client: AsyncOpenAI, image: Path) -> Verdict:
    check = await client.content_provenance_checks.create(
        file=(image.name, image.read_bytes(), mimetypes.guess_type(image)[0])
    )
    signals = {r.type: r for r in check.results}
    return Verdict(
        synthid=signals["synthid"].outcome == "detected",
        detail=", ".join(f"{r.type}: {r.outcome}" + (f" ({r.model})" if r.model else "") for r in check.results),
    )


async def ask_model(client: AsyncOpenAI, model: str, image: Path) -> Verdict:
    data = base64.b64encode(image.read_bytes()).decode()
    completion = await client.chat.completions.parse(
        model=model,
        response_format=Verdict,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:{mimetypes.guess_type(image)[0]};base64,{data}"}},
                ],
            }
        ],
    )
    return completion.choices[0].message.parsed


def make_detector(name: str) -> Detector:
    if name == PROVENANCE:
        client = AsyncOpenAI(max_retries=MAX_RETRIES)
        return lambda image: check_provenance(client, image)
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        max_retries=MAX_RETRIES,
    )
    return lambda image: ask_model(client, name, image)


async def evaluate(folder: Path, names: list[str], concurrency: int, out: Path) -> None:
    images = sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES)
    if not images:
        raise SystemExit(f"no images found in {folder}")

    detectors = {name: make_detector(name) for name in names}
    limit = asyncio.Semaphore(concurrency)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w") as f:

        async def run(name: str, image: Path) -> None:
            row = {"image": str(image.relative_to(folder)), "detector": name}
            async with limit:
                try:
                    row |= (await detectors[name](image)).model_dump()
                except Exception as e:
                    row["error"] = repr(e)
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(f"{name} {row['image']}: {row.get('synthid', 'error')}")

        await asyncio.gather(*(run(n, i) for n in names for i in images))

    print(f"wrote {len(images) * len(names)} results to {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check every image in a folder for SynthID.")
    parser.add_argument("folder", type=Path)
    parser.add_argument(
        "--detectors",
        default=PROVENANCE,
        help=f"comma-separated: {PROVENANCE} and/or OpenRouter model ids such as google/gemini-3.8-flash",
    )
    parser.add_argument("--concurrency", type=int, default=16, help="max requests in flight")
    parser.add_argument("--out", type=Path, help="results file (default: results/<timestamp>.jsonl)")
    args = parser.parse_args()

    out = args.out or Path("results") / f"{datetime.now():%Y%m%d-%H%M%S}.jsonl"
    asyncio.run(evaluate(args.folder, args.detectors.split(","), args.concurrency, out))


if __name__ == "__main__":
    main()
