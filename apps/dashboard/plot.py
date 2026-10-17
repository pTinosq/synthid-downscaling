import sys
from pathlib import Path

import results

for path in map(Path, sys.argv[1:]):
    out = path.with_suffix(".png")
    results.plot(results.load(path)).savefig(out, dpi=150)
    print(f"wrote {out}")
