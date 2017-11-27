FROM alpine:latest

RUN apk add --update py-pip
RUN apk add openssl libc-dev python-dev gcc
RUN pip install --upgrade pip
ADD . /usr/src/app
WORKDIR /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "/usr/src/app/worker.py"]
