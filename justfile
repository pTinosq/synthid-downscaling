set dotenv-load

default:
    @just --list

# Downscale an image into data/images/<name>, e.g. just prepare cat.png -methods lanczos,box -step 5
prepare image *flags:
    cd apps/prepare && go run . -out "{{justfile_directory()}}/data/images/{{file_stem(image)}}" {{flags}} "{{absolute_path(join(invocation_directory(), image))}}"

# Ask each model whether the images in data/images/<name> carry SynthID
evals name *flags:
    cd apps/evals && uv run evals.py "{{justfile_directory()}}/data/images/{{name}}" --out "{{justfile_directory()}}/data/results/{{name}}/$(date +%Y%m%d-%H%M%S).jsonl" {{flags}}

# Open the results dashboard in the browser
dashboard:
    cd apps/dashboard && uv run streamlit run app.py

# Render detection-rate charts next to each results file, e.g. just plot data/results/cat/*.jsonl
plot +results:
    uv run --project apps/dashboard apps/dashboard/plot.py {{results}}
