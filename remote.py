#!/bin/python3

from time import time
from random import shuffle, randint

import socket
import csv
from os import path, listdir, mkdir
from typing import Union, List, Tuple

import numpy as np
import tensorflow as tf
from pynput.mouse import Controller, Button


class Connection:
    MAIN_RELEASE_MSG = 'end'
    SEC_PRESS_MSG = 'spec'
    SEC_RELEASE_MSG = 'rel'

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
        # or by better coding
        # returns string or tuple of two lists of floats
        data, _ = self.s.recvfrom()
        data = data.decode()

        assert data.startswith(':'), "Unexpected data recieved"
        data = data[1:]

        if data in (self.MAIN_RELEASE_MSG, self.SEC_PRESS_MSG, self.SEC_RELEASE_MSG):
            return data  # type: str
        else:
            data = data.split(':')
            data = [float(x) for x in data]
            acc, gyro = data[:3], data[3:]
            return acc, gyro  # type: tuple of lists

    def receive_char(self, char: str) -> List[str, List[List[float]]]:
        accepted_chars = ['-', '_'] + [chr(i) for i in range(ord('A'), ord('Z')+1)]
        assert len(char) == 1, "char has to be single character"
        assert char in accepted_chars, "accepted: A-Z, '-', '_'"

        data_list = []
        while True:
            data = self.receive_data()
            if type(data) == tuple:
                data_list.append(data[0])
            elif data == self.MAIN_RELEASE_MSG:
                break

        return [char, data_list]


class Training:
    def __init__(self, data_path='train_char/',
                 max_input_len=400,
                 include_extra_chars=True,
                 ) -> None:
        if not path.exists(data_path):
            mkdir(data_path)
        self.data_path = data_path
        self.max_input_len = max_input_len
        self.include_extra_chars = include_extra_chars

        self.train_labels = None
        self.train_values = None

    def _write_to_file(self) -> None:
        pass

    def collect_data(self) -> None:
        pass

    def prepare_data(self) -> Tuple[np.array]:
        pass

    def train(self) -> None:
        pass
