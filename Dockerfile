FROM python:3

MAINTAINER Cédric HT

WORKDIR /usr/src/app
COPY portacl.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./portacl.py"]
