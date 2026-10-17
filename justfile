set dotenv-load

default:
    @just --list

# Downscale an image into data/images/<name>, e.g. just prepare cat.png -methods lanczos,box -step 5
prepare image *flags:
    cd apps/prepare && go run . -out "{{justfile_directory()}}/data/images/{{file_stem(image)}}" {{flags}} "{{absolute_path(image)}}"
