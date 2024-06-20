import cv2 as cv
import socket
import numpy as np
import struct
from threading import Thread, Event
import time

class UDPStream:
    def __init__(self, ip, port)->None:
        self.__ip = ip
        self.__port = port
        self.__payload_size = struct.calcsize("L")
        self.__frames_buffer = []
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.__server_socket.bind((self.__ip, self.__port))
        self.__server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__exit_event = Event()
        self.__worker_thread = None
        self.MAX_DGRAM = 65000


    def __run(self)->None:
        while not self.__exit_event.is_set():
            if len(self.__frames_buffer) > 0:
                frame = self.__frames_buffer.pop(0)
                self.__chuck_frame(frame)

    def __chuck_frame(self, frame)->list:
        # Encode the frame in JPEG format
        encoded, buffer = cv.imencode('.jpg', frame)
        if encoded:
            data = buffer.tobytes()
            # Break the frame into chunks
            size = len(data)
            num_chunks = size // self.MAX_DGRAM + 1

            for i in range(num_chunks):
                chunk = data[i*self.MAX_DGRAM:(i+1)*self.MAX_DGRAM]
                self.__server_socket.sendto(struct.pack("B", i) + chunk, (self.__ip, self.__port))             


    def start(self)->None:
        if self.__worker_thread is None:
            self.__worker_thread = Thread(target=self.__run)
            self.__worker_thread.start()
    
    def stop(self)->None:
        self.__exit_event.set()
        self.__server_socket.close()
        self.__worker_thread.join()

    def queue_frame(self, frame)->None:
        self.__frames_buffer.append(frame)