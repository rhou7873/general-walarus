FROM python:3.11
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get -y install ffmpeg

COPY osdk ./osdk
RUN chmod +x ./osdk/generate_osdk.sh
RUN --mount=type=secret,id=osdk_generate_token \
    --mount=type=secret,id=osdk_index_url \
    --mount=type=secret,id=osdk_extra_index_url \
    OSDK_GENERATE_TOKEN="$(cat /run/secrets/osdk_generate_token)" \
    OSDK_INDEX_URL="$(cat /run/secrets/osdk_index_url)" \
    OSDK_EXTRA_INDEX_URL="$(cat /run/secrets/osdk_extra_index_url)" \
    ./osdk/generate_osdk.sh

COPY . .

EXPOSE 8000

CMD [ "python", "-u", "run.py" ]
