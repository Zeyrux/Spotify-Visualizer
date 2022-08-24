FROM python

WORKDIR /app

ADD . /app

RUN apt-get update
RUN apt-get install -y ffmpeg
RUN pip install -r requirements.txt

CMD ["uwsgi", "app.ini"]