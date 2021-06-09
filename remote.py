#!/bin/python3

from time import time
from random import shuffle, randint

import socket
import csv
from os import path, listdir, mkdir
from typing import Union, List, Tuple

import numpy as np
from numpy.core.defchararray import array
import tensorflow as tf
from pynput.mouse import Controller, Button

from dataclasses import dataclass

from tensorflow.python.distribute import parameter_server_strategy


@dataclass
class CharSignal:
    """Stores accelerometer readings of character and name of character."""
    char: str
    signal: List[List[float]]

    def set_length(self, new_length) -> None:
        if len(self.signal) > new_length:
            self.signal = self.signal[:new_length]
        elif len(self.signal) < new_length:
            len_diff = new_length-len(self.signal)
            self.signal += [[.0, .0, .0] for _ in range(len_diff)]

    def get_array(self) -> np.array:
        return np.array(self.signal)


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
        self._remote_addr = (remote_ip, remote_port)
        self._server_addr = (server_ip, server_port)

        self._s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._s.bind(self._server_addr)

    def send_ready_signal(self) -> None:
        self._s.sendto(bytes(1), self._remote_addr)

    def receive_data(self) -> Union[Tuple[List[float], List[float]], str]:
        # hopefully to be nicely fixed in python 3.10
        # or by better coding
        # returns string or tuple of two lists of floats
        data, _ = self._s.recvfrom()
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

    def receive_char(self, char: str) -> CharSignal:
        accepted_chars = ['-', '_']
        accepted_chars += [chr(i) for i in range(ord('A'), ord('Z')+1)]

        assert len(char) == 1, "char has to be single character"
        assert char in accepted_chars, "accepted: A-Z, '-', '_'"

        data_list = []
        while True:
            data = self.receive_data()
            if type(data) == tuple:
                data_list.append(data[0])
            elif data == self.MAIN_RELEASE_MSG:
                break

        return CharSignal(char, data_list)


class Training:
    def __init__(self, data_path: str = 'train_char/',
                 max_input_len: int = 400,
                 ) -> None:
        if not path.exists(data_path):
            mkdir(data_path)

        if not data_path.endswith('/'):
            data_path += '/'

        self._data_path = data_path
        self.max_input_len = max_input_len

        self._train_labels = None
        self._train_values = None

        self.training_seq = None

    def set_training_seq(self,
                         chars: list = None,
                         repeats: int = 40,
                         shuffle_chars: bool = False,
                         include_extra_chars: bool = True) -> int:
        if chars is None:
            chars = [chr(i) for i in range(ord('A'), ord('Z')+1)]
        if include_extra_chars:
            chars += ['-', '_']
        chars = chars * repeats
        if shuffle_chars:
            shuffle(chars)

        self.training_seq = chars
        return len(chars)

    def get_next_training_char(self) -> str:
        pass

    def _next_file_no(self, char) -> int:
        """Returns next unused signal number in dir of data_path."""
        all_files = listdir(self._data_path)
        max_no = -1
        for file in all_files:
            file_no = int(file[1:])
            if file[0] == char and file_no > max_no:
                max_no = file_no
        return max_no + 1

    def write_to_dataset(self, char_signal: CharSignal) -> None:
        """Saves signal to new file"""
        # char_signal.set_length(self.max_input_len)
        char = char_signal.char
        file_name = self._data_path + char + self._next_file_no(char) + '.csv'
        with open(file_name, mode='w') as data_file:
            data_writer = csv.writer(data_file)
            data_writer.writerows(char_signal.signal)

    def prepare_data(self) -> int:
        """Returns number of signal files processed.
        Sets self._train_values, self._train_labels."""
        data = []
        for file_name in listdir(self._data_path):
            assert file_name.endswith('.csv'), "Non-csv file in data directory"
            with open(file_name) as data_file:
                csv_reader = csv.reader(data_file)
                row_list = [[float(x) for x in row] for row in csv_reader]
                char_signal = CharSignal(file_name[0], row_list)
                char_signal.set_length(self.max_input_len)
                data.append(char_signal)
        shuffle(data)
        for char_signal in data:
            self._train_labels.append(ord(char_signal.char)-ord('A'))
            self._train_values.append(char_signal.signal)
        self._train_labels = np.array(self._train_labels)
        self._train_values = np.array(self._train_values)

        return len(data)

    def train(self) -> None:
        assert type(self._train_values) == np.array
        assert type(self._train_labels) == np.array

        model = tf.keras.Sequential([
            tf.keras.layers.Flatten(input_shape=(self.max_input_len, 3)),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(4)
        ])
        model.compile(optimizer='adam',
                      loss=tf.keras.losses.SparseCategoricalCrossentropy(
                          from_logits=True),
                      metrics=['accuracy'])
        model.fit(self._train_values, self._train_labels, epochs=10)


class Control:
    def __init__(self,
                 mode: str = "gyro",
                 accel_multiplier: float = 2.5,
                 accel_treshold: float = .7,
                 gyro_multiplier: float = 8,
                 gyro_treshold: float = .1,
                 double_click_time: float = .3) -> None:
        self.mode = mode
        self.accel_multiplier = accel_multiplier
        self.accel_treshold = accel_treshold
        self.gyro_multiplier = gyro_multiplier
        self.gyro_treshold = gyro_treshold
        self.double_click_time = double_click_time

        self._last_click_time = None

        mouse = Controller()

        def move(self, data: Union[Tuple[List[float], List[float]], str]) -> Union[str, None]:
            if type(data) == str:
                return data

        def calibrate(self):
            pass
