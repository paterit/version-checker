FROM python:3.7-alpine3.8

# update apk repo
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.8/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.8/community" >> /etc/apk/repositories

RUN apk update
RUN apk add bash make

RUN pip install pipenv

RUN echo 'eval "$(pipenv --completion)"' > /root/.bashrc

ENV PIPENV_VENV_IN_PROJECT=1
