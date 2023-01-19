FROM python:3.7

ADD DataStorage.py /

RUN python -m pip install --upgrade pip \ 
    pip install mysql-connector-python\
    pip install confluent-kafka

CMD  ["python", "./DataStorage.py" ]