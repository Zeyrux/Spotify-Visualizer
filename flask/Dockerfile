FROM python:3.10.4

EXPOSE 5000

WORKDIR /app

ADD . /app

RUN apt-get update
RUN apt-get install -y ffmpeg
RUN sed -i 's/var_regex = re.compile(^\w+\W)/var_regex = re.compile(r"^\$*\w+\W")/g' /usr/local/lib/python3.10/site-packages/pytube/cipher.py
RUN pip install -r requirements.txt

CMD ["uwsgi", "app.ini"]