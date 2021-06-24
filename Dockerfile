FROM python:3.9
COPY . .
RUN pip install --no-cache-dir paho-mqtt
ENTRYPOINT ["python", "-u", "./mqttlogger.py"]
