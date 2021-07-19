# Time clock a RaspberryPi project
- to get an overview of the daily working time
- check_in/check_out via RC522 module

## Tech stack
- Tornado webserver for async request/response
- SQLAlchemy and simple sql DB
- Frontend via (HTMX)[https://htmx.org/docs/]
- Webserver <-> RC522 communication via C++


## How to compile requirements
```bash
pip-compile --generate-hashes requirements.in

python -m pip install \
        --no-deps \
        --no-cache-dir \
        --require-hashes \
        --progress-bar=off \
        -r /requirements/requirements.txt
```