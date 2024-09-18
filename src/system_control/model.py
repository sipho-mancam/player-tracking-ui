from confluent_kafka import Consumer, KafkaException, KafkaError
import json
import threading

class ColorPaletteListener:
    def __init__(self, topic, bootstrap_servers='localhost:9092', group_id='color_palette_group'):
        self.topic = topic
        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        })
        self.__listener = None

        self.thread = threading.Thread(target=self.listen)
        self.thread.daemon = True
        self.thread.start()

    def listen(self):
        self.consumer.subscribe([self.topic])
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        continue
                        # raise KafkaException(msg.error())
                data = json.loads(msg.value().decode('utf-8'))
                if 'color_palette' in data:
                    color_palette = self.parse_color_palette(data['color_palette'])
                    if self.__listener is not None:
                        self.__listener(*(color_palette, ))
        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()


    def register_listener(self, listener)->None:
        self.__listener = listener

    @staticmethod
    def parse_color_palette(color_palette):
        return [tuple(color) for color in color_palette]

if __name__ == "__main__":
    listener = ColorPaletteListener(topic='system-control')
    listener.listen()
