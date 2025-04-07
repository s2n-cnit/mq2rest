FROM python:3.13.2-bullseye

RUN pip install poetry

RUN mkdir ./mq2rest
WORKDIR /mq2rest

COPY ./* ./

RUN poetry install --no-root

CMD ["poetry", "run", "python", "main.py"]
