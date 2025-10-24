FROM python:3.12
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get -y install ffmpeg

COPY . .

CMD [ "python", "-u", "run.py" ]
