import streamlit as st

import results

st.set_page_config(page_title="SynthID downscaling", layout="wide")

sets = sorted(results.DATA.glob("results/*.jsonl"))
if not sets:
    st.info(f"No results yet. Run `just evals <name>` to populate {results.DATA / 'results'}.")
    st.stop()

path = st.sidebar.selectbox("Image set", sets, format_func=lambda p: p.stem)
images = results.DATA / "images" / path.stem
df = results.load(path)

st.title(path.stem)
st.pyplot(results.plot(df))
st.subheader("Breakdown")
st.dataframe(results.breakdown(df))

st.subheader("Checked images")
method = st.selectbox("Method", sorted(set(df["method"]) - {"original"}))
rows = df[df["method"].isin([method, "original"])].sort_values("scale", ascending=False)
for col, row in zip(st.columns(4) * (len(rows) // 4 + 1), rows.itertuples()):
    col.image(str(images / row.image), caption=f"{row.scale}% · {'SynthID' if row.synthid else 'no SynthID'}")
    col.caption(row.detail)
