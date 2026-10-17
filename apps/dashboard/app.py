import streamlit as st

import results

st.set_page_config(page_title="SynthID downscaling", layout="wide")

runs = sorted(results.DATA.glob("results/*/*.jsonl"), reverse=True)
if not runs:
    st.info(f"No results yet. Run `just evals <name>` to populate {results.DATA / 'results'}.")
    st.stop()

run = st.sidebar.selectbox("Run", runs, format_func=lambda p: f"{p.parent.name} / {p.stem}")
images = results.DATA / "images" / run.parent.name
df = results.load(run)

st.title(run.parent.name)
if "error" in df and (errors := df["error"].notna().sum()):
    st.warning(f"{errors} of {len(df)} requests failed.")

st.pyplot(results.plot(df))
st.subheader("Breakdown scale")
st.caption("Largest scale at which detection fails.")
st.dataframe(results.breakdown(df))

st.subheader("Images")
method = st.selectbox("Method", sorted(set(df["method"]) - {"original"}))
rows = df[df["method"].isin([method, "original"])].sort_values("scale", ascending=False)
for col, row in zip(st.columns(4) * (len(rows) // 4 + 1), rows.itertuples()):
    verdict = {True: "SynthID", False: "no SynthID"}.get(row.synthid, "error")
    col.image(str(images / row.image), caption=f"{row.scale}% · {verdict}")
    if isinstance(row.detail, str):
        col.caption(row.detail)
