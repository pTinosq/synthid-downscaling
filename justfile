set dotenv-load

default:
    @just --list

# Downscale an image into data/images/<name>, e.g. just prepare gemini_dog.jpeg -methods lanczos,box -step 5
prepare image *flags:
    cd apps/prepare && go run . -out "{{justfile_directory()}}/data/images/{{file_stem(image)}}" {{flags}} "{{absolute_path(join(invocation_directory(), image))}}"

# Check data/images/<name> for SynthID into data/results/<name>.jsonl, skipping images already checked
evals name *flags:
    cd apps/evals && uv run evals.py "{{justfile_directory()}}/data/images/{{name}}" "{{justfile_directory()}}/data/results/{{name}}.jsonl" {{flags}}

# Open the results dashboard in the browser
dashboard:
    cd apps/dashboard && uv run streamlit run app.py

# Save the detection-rate chart for data/results/<name>.jsonl as data/results/<name>.png
plot name:
    uv run --project apps/dashboard apps/dashboard/plot.py "data/results/{{name}}.jsonl"
