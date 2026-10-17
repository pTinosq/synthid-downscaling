from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

DATA = Path(__file__).resolve().parents[2] / "data"


def load(path: Path) -> pd.DataFrame:
    df = pd.read_json(path, lines=True)
    for column in ("synthid", "detail"):
        if column not in df:
            df[column] = pd.NA
    parts = df["image"].str.split("/")
    df["method"] = parts.map(lambda p: p[0] if len(p) > 1 else "original")
    df["scale"] = parts.map(lambda p: int(Path(p[-1]).stem) if len(p) > 1 else 100)
    return df


def detection_rates(df: pd.DataFrame) -> pd.DataFrame:
    answered = df.dropna(subset=["synthid"]).astype({"synthid": float})
    return answered.groupby(["method", "scale"], as_index=False)["synthid"].mean()


def breakdown(df: pd.DataFrame) -> pd.Series:
    """Largest scale at which SynthID stops being detected, per method."""
    rates = detection_rates(df)
    missed = rates[(rates["synthid"] < 0.5) & (rates["method"] != "original")]
    return missed.groupby("method")["scale"].max().rename("breakdown scale (%)")


def plot(df: pd.DataFrame) -> Figure:
    fig = Figure(figsize=(8, 4), layout="constrained")
    ax = fig.subplots()
    for method, group in detection_rates(df).groupby("method"):
        if method == "original":
            ax.axhline(group["synthid"].iloc[0], color="black", linestyle="--", label=method)
        else:
            ax.plot(group["scale"], group["synthid"], marker="o", label=method)
    ax.set(xlabel="scale (%)", ylabel="SynthID detection rate", ylim=(-0.05, 1.05))
    ax.invert_xaxis()
    if ax.lines:
        ax.legend(loc="lower left")
    return fig
