FROM python:3.10
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get -y install ffmpeg

ENV CMD_PREFIX=+
ENV ENV_NAME=production

COPY . .

CMD [ "python", "./run.py" ]
