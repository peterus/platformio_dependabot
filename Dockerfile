FROM python:3.14

LABEL org.opencontainers.image.source=https://github.com/peterus/platformio_dependabot
LABEL org.opencontainers.image.description="A Dependabot like GitHub Action for PlatformIO"
LABEL org.opencontainers.image.licenses=MIT

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

COPY /platformio_dependabot /app/platformio_dependabot
COPY entrypoint.sh /app/entrypoint.sh
