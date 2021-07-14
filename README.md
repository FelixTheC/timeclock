pip-compile --generate-hashes requirements.in

RUN python -m pip install \
        --no-deps \
        --no-cache-dir \
        --require-hashes \
        --progress-bar=off \
        -r /requirements/requirements.txt