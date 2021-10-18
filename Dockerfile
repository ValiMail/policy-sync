FROM python:3.9-bullseye
WORKDIR /usr/src

ENV CRYPTO_PATH=/etc/dane_id/
ENV APP_UID=0
ENV DEBIAN_FRONTEND=noninteractive
ENV POLICY_FILE_DIR=/var/valimail_policy

COPY ./app /usr/src/

COPY app/depends/ /tmp/depends/

RUN apt-get update && \
    cat /tmp/depends/os_packages | xargs apt-get install -y

RUN pip3 install --upgrade pip
RUN pip3 install -r /tmp/depends/requirements.txt

RUN mkdir -p POLICY_FILE_DIR

CMD unbuffer python3 application.py