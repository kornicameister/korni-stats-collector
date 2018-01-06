FROM python:3.7-rc

WORKDIR /usr/src/app

COPY requirements.txt setup.py ksc/ ./

RUN apt-get -q update && \
    apt-get -qy install \
        python-dev \
        gcc \
        make

RUN pip install -U pip && \
    pip install --no-cache-dir -r requirements.txt

ENV python ksc/main.py collect
