FROM python:3.6

WORKDIR /app

RUN pip install awscli
RUN apt-get update  && apt-get install vim zip -y

COPY requirements.txt .

RUN pip install -r requirements.txt

ENTRYPOINT bash
