FROM python:3.7

ADD DataRetrieval.py /

RUN pip install Flask\
    pip install mysql-connector-python

CMD  ["python", "./DataRetrieval.py" ]