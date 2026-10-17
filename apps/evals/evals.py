import argparse
import asyncio
import base64
import json
import mimetypes
import os
from datetime import datetime
from pathlib import Path

from openai import AsyncOpenAI
from pydantic import BaseModel

DEFAULT_MODELS = ["google/gemini-4-argon", "google/gemini-3.8-flash", "openai/gpt-6.1-sol"]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
PROMPT = (
    "Check this image for a SynthID watermark. "
    "Answer synthid=true only if you detect SynthID, and briefly explain your reasoning."
)


class Verdict(BaseModel):
    synthid: bool
    reasoning: str


async def classify(client: AsyncOpenAI, model: str, image: Path) -> Verdict:
    mime = mimetypes.guess_type(image)[0]
    data = base64.b64encode(image.read_bytes()).decode()
    completion = await client.chat.completions.parse(
        model=model,
        response_format=Verdict,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}},
                ],
            }
        ],
    )
    return completion.choices[0].message.parsed


async def evaluate(folder: Path, models: list[str], concurrency: int, out: Path) -> None:
    images = sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES)
    if not images:
        raise SystemExit(f"no images found in {folder}")

    client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])
    limit = asyncio.Semaphore(concurrency)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w") as f:

        async def run(model: str, image: Path) -> None:
            row = {"image": str(image.relative_to(folder)), "model": model}
            async with limit:
                try:
                    row |= (await classify(client, model, image)).model_dump()
                except Exception as e:
                    row["error"] = repr(e)
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(f"{model} {row['image']}: {row.get('synthid', 'error')}")

        await asyncio.gather(*(run(m, i) for m in models for i in images))

    print(f"wrote {len(images) * len(models)} results to {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask LLMs whether each image in a folder carries SynthID.")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS), help="comma-separated OpenRouter model ids")
    parser.add_argument("--concurrency", type=int, default=16, help="max requests in flight")
    parser.add_argument("--out", type=Path, help="results file (default: results/<timestamp>.jsonl)")
    args = parser.parse_args()

    out = args.out or Path("results") / f"{datetime.now():%Y%m%d-%H%M%S}.jsonl"
    asyncio.run(evaluate(args.folder, args.models.split(","), args.concurrency, out))


if __name__ == "__main__":
    main()
