import paho.mqtt.client as mqtt
import time
import threading
import os
import signal

class MQTTLogger:

    def __init__(self, topic:str, hostname:str):
        self._topic = topic
        self._hostname = hostname
        self._client = mqtt.Client(clean_session=True)
        self._client.connect(self._hostname)
        self._is_running = False
    
    def start_logging(self):
        x = threading.Thread(target=self.log)
        x.start()
    
    def log_message(self, client, userdata, message):
        provided_path = os.environ.get('LOGGING_FILE_PATH')
        if provided_path:
            with open(f"{provided_path}/{self._topic}.csv", 'a+') as file:
                file.writelines(str(message.payload.decode("utf-8")) + "\n")
        else:
            with open(f"{os.getcwd()}/{self._topic}.csv", 'a+') as file:
                file.writelines(str(message.payload.decode("utf-8")) + "\n")
    
    def log(self):
        self._is_running = True
        self._client.loop_start()
        self._client.subscribe(self._topic)
        self._client.on_message = self.log_message
        logging.info(f"Started logging topic {self._topic}")
        while(self._is_running):
            time.sleep(1)
        self._client.loop_stop()
        logging.info(f"Stopped logging topic {self._topic}")
    
    def stop_logging(self):
        self._is_running = False


if __name__ == "__main__":
    import logging
    import sys

    #Configure logging
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


    loggers = []
    escape = False
    provided_hostname = os.environ.get('LOGGING_MQTT_HOST')

    #Gracefully stop application when docker container is interrupted/stopped
    def handle_sigterm(*args):
        logging.info("Stopping container")
        global escape
        escape = True

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    def add_topic(hostname:str, topic_name:str=None):
        if not topic_name:
            topic_name = input('\nTopic name: ')                                                               
        logger = MQTTLogger(topic_name, hostname)                                                              
        logger.start_logging()
        loggers.append(logger)


    if not provided_hostname:
        #Running in interactive mode
        hostname = input("Enter the hostname of the MQTT Broker: ")

        if os.path.isfile(os.getcwd() + "/.topics"):
            logging.info("Adding topics from .topics file")
            with open(os.getcwd() + "/.topics", 'r') as file:
                for line in file:
                    stripped_line = line.strip()
                    add_topic(hostname, stripped_line)
        else:
            logging.info("No .topics file provided. Add topics manually.")
            add_topic()

        while not escape:
            time.sleep(1)
            i = input('#'*40 + '\n(a) Add new topic that should be logged\n(s) Stop logging\n(a/s): ')
            if i == 's':
                for logger in loggers:
                    logger.stop_logging()
                escape = True
            elif i== 'a':
                add_topic()
    else:
        #Running in standalone mode (docker container)
        if os.path.isfile(os.getcwd() + "/.topics"):
            logging.info("Adding topics from .topics file")
            with open(os.getcwd() + "/.topics", 'r') as file:
                for line in file:
                    stripped_line = line.strip()
                    add_topic(provided_hostname, stripped_line)
        else:
            logging.info("No .topics file provided.")

        while not escape:
            time.sleep(1)

        logging.info("Stopping loggers")
        for logger in loggers:
            logger.stop_logging()