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
    return answered.groupby(["model", "method", "scale"], as_index=False)["synthid"].mean()


def breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Largest scale at which each model stops detecting SynthID, per method."""
    rates = detection_rates(df)
    missed = rates[(rates["synthid"] < 0.5) & (rates["method"] != "original")]
    return missed.groupby(["model", "method"])["scale"].max().unstack("method")


def plot(df: pd.DataFrame) -> Figure:
    rates = detection_rates(df)
    models = sorted(rates["model"].unique())
    fig = Figure(figsize=(6 * len(models), 4), layout="constrained")
    axes = fig.subplots(1, len(models), sharey=True, squeeze=False)[0]
    for ax, model in zip(axes, models):
        for method, group in rates[rates["model"] == model].groupby("method"):
            if method == "original":
                ax.axhline(group["synthid"].iloc[0], color="black", linestyle="--", label=method)
            else:
                ax.plot(group["scale"], group["synthid"], marker="o", label=method)
        ax.set(title=model, xlabel="scale (%)", ylim=(-0.05, 1.05))
        ax.invert_xaxis()
    axes[0].set_ylabel("SynthID detection rate")
    axes[-1].legend(loc="lower left")
    return fig
