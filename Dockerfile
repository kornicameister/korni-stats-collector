FROM python:3.7.0

WORKDIR /usr/src/app
ENV PYTHONPATH=/usr/src/app

RUN apt-get -q update && \
    apt-get -qy --no-install-recommends install \
        python-dev \
        gcc \
        make && \
    apt-get autoclean && \
    apt-get autoremove && \
    rm -rf /etc/apt/sources.list.d

COPY README.md requirements.txt setup.py ./
COPY ksc/ ./ksc/

RUN pip install -U pip && \
    pip install --no-cache-dir -r requirements.txt

RUN python setup.py install

ENTRYPOINT ["python", "ksc/main.py"]
CMD ["--help"]
