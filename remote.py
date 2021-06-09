#!/bin/python3

from time import time
from random import shuffle, randint

import socket
import csv
from os import path, listdir, mkdir
from typing import Union, List, Tuple

import numpy as np
import tensorflow as tf


class Connection:
    MAIN_RELEASE_MSG = "end"
    SEC_PRESS_MSG = "spec"
    SEC_RELEASE_MSG = "rel"

    def __init__(self,
                 remote_ip='192.168.1.230',
                 remote_port=2999,
                 server_ip='192.168.1.100',
                 server_port=3999,
                 ) -> None:
        self.remote_addr = (remote_ip, remote_port)
        self.server_addr = (server_ip, server_port)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(self.server_addr)

    def send_ready_signal(self) -> None:
        self.s.sendto(bytes(1), self.remote_addr)

    def receive_data(self) -> Union[Tuple[List[float], List[float]], str]:  
        # hopefully to be nicely fixed in python 3.10
        data, _ = self.s.recvfrom()
        data = data.decode()

        assert data.startswith(":"), "Unexpected data recieved"
        data = data[1:]

        if data == self.MAIN_RELEASE_MSG:
            return "main_rel"
        elif data == self.SEC_PRESS_MSG:
            return "sec_press"
        elif data == self.SEC_RELEASE_MSG:
            return "sec_rel"
        else:
            data = data.split(":")
            data = [float(x) for x in data]
            acc, gyro = data[:3], data[3:]
            return acc, gyro

class Training:
    pass
