from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

DATA = Path(__file__).resolve().parents[2] / "data"


def load(path: Path) -> pd.DataFrame:
    df = pd.read_json(path, lines=True)
    if "synthid" not in df:
        df["synthid"] = pd.NA
    parts = df["image"].str.split("/")
    df["method"] = parts.map(lambda p: p[0] if len(p) > 1 else "original")
    df["scale"] = parts.map(lambda p: int(Path(p[-1]).stem) if len(p) > 1 else 100)
    return df


def detection_rates(df: pd.DataFrame) -> pd.DataFrame:
    answered = df.dropna(subset=["synthid"]).astype({"synthid": float})
    return answered.groupby(["detector", "method", "scale"], as_index=False)["synthid"].mean()


def breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Largest scale at which each detector stops detecting SynthID, per method."""
    rates = detection_rates(df)
    missed = rates[(rates["synthid"] < 0.5) & (rates["method"] != "original")]
    return missed.groupby(["detector", "method"])["scale"].max().unstack("method")


def plot(df: pd.DataFrame) -> Figure:
    rates = detection_rates(df)
    detectors = sorted(rates["detector"].unique())
    fig = Figure(figsize=(6 * len(detectors), 4), layout="constrained")
    axes = fig.subplots(1, len(detectors), sharey=True, squeeze=False)[0]
    for ax, detector in zip(axes, detectors):
        for method, group in rates[rates["detector"] == detector].groupby("method"):
            if method == "original":
                ax.axhline(group["synthid"].iloc[0], color="black", linestyle="--", label=method)
            else:
                ax.plot(group["scale"], group["synthid"], marker="o", label=method)
        ax.set(title=detector, xlabel="scale (%)", ylim=(-0.05, 1.05))
        ax.invert_xaxis()
    axes[0].set_ylabel("SynthID detection rate")
    axes[-1].legend(loc="lower left")
    return fig
