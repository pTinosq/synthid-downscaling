from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

DATA = Path(__file__).resolve().parents[2] / "data"


def load(path: Path) -> pd.DataFrame:
    df = pd.read_json(path, lines=True)
    if "synthid" not in df:
        return pd.DataFrame(columns=["image", "synthid", "detail", "method", "scale"])
    df = df.dropna(subset=["synthid"]).drop_duplicates("image", keep="last").astype({"synthid": bool})
    parts = df["image"].str.split("/")
    df["method"] = parts.map(lambda p: p[0] if len(p) > 1 else "original")
    df["scale"] = parts.map(lambda p: int(Path(p[-1]).stem) if len(p) > 1 else 100)
    return df


def breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """The boundary between the smallest detected and the largest undetected scale, per method."""
    downscaled = df[df["method"] != "original"]
    return pd.DataFrame(
        {
            "detected down to (%)": downscaled[downscaled["synthid"]].groupby("method")["scale"].min(),
            "lost at (%)": downscaled[~downscaled["synthid"]].groupby("method")["scale"].max(),
        }
    ).astype("Int64")


def plot(df: pd.DataFrame) -> Figure:
    downscaled = df[df["method"] != "original"]
    methods = sorted(downscaled["method"].unique())
    fig = Figure(figsize=(8, 1.5 + 0.4 * len(methods)), layout="constrained")
    ax = fig.subplots()
    for detected, color, label in [(True, "tab:green", "detected"), (False, "tab:red", "not detected")]:
        points = downscaled[downscaled["synthid"] == detected]
        ax.scatter(points["scale"], points["method"].map(methods.index), color=color, label=label)
    ax.set(yticks=range(len(methods)), yticklabels=methods, xlabel="scale (%)", xlim=(0, 100))
    ax.invert_yaxis()
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    return fig
