FROM python:3

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

COPY /platformio_dependabot /app
COPY entrypoint.sh /app/entrypoint.sh
