#!/bin/python3

from connect import ConnectRemote
from time import time
from random import shuffle

import socket
import csv
from os import path, listdir, mkdir
from typing import Union, List, Tuple

import numpy as np
from numpy.core.defchararray import array
import tensorflow as tf
from tensorflow.python.distribute import parameter_server_strategy
from pynput.mouse import Controller, Button

from dataclasses import dataclass


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

    def get_array(self) -> np.ndarray:
        return np.array(self.signal)


@dataclass
class SensorConfig:
    mode: str = 'gyro'
    accel_multiplier: float = 2.5
    accel_treshold: float = .7
    gyro_multiplier: float = 8
    gyro_treshold: float = .1
    double_click_time: float = .3


@dataclass
class ConnectionConfig:
    remote_ip: str = '192.168.1.230'
    remote_port: int = 2999
    server_ip: str = '192.168.1.100'
    server_port: int = 3999

    @property
    def server_addr(self) -> Tuple[str, int]:
        return (self.server_ip, self.server_port)

    @property
    def remote_addr(self) -> Tuple[str, int]:
        return (self.remote_ip, self.remote_port)


@dataclass
class TrainingConfig:
    max_input_len: int = 400
    _training_data_path: str = 'train_char/'

    @property
    def training_data_path(self):
        return self._training_data_path

    @training_data_path.setter
    def training_data_path(self, new_path: str):
        if not new_path.endswith('/'):
            new_path += '/'
        self._training_data_path = new_path


class Remote:
    MAIN_RELEASE_MSG = 'end'
    SEC_PRESS_MSG = 'spec'
    SEC_RELEASE_MSG = 'rel'

    def __init__(self,
                 sensor_config: SensorConfig,
                 conn_config: ConnectionConfig,
                 training_config: TrainingConfig) -> None:

        self.sensor_config = sensor_config
        self.conn_config = conn_config
        self.training_config = training_config

        self._s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._s.bind(self.conn_config.server_addr)

        if not path.exists(self.training_config.training_data_path):
            mkdir(self.training_config.training_data_path)

        self._train_labels = None
        self._train_values = None
        self.training_sequence = None
        self._model = None

    def send_ready_signal(self) -> None:
        self._s.sendto(bytes(1), self.conn_config.remote_addr)

    def receive_data(self) -> Union[Tuple[List[float], List[float]], str]:
        data, _ = self._s.recvfrom(256)
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
        accepted_chars = ['-', '_', '?']
        accepted_chars += [chr(i) for i in range(ord('A'), ord('Z')+1)]

        assert len(char) == 1, "char has to be single character"
        assert char in accepted_chars, "accepted: A-Z, '-', '_', '?'"

        data_list = []
        while True:
            data = self.receive_data()
            if type(data) == tuple:
                data_list.append(data[0])
            elif data == self.MAIN_RELEASE_MSG:
                break

        return CharSignal(char, data_list)

    def move_cursor(self) -> None:
        pass

    def _prepare_char(self, data) -> np.ndarray:
        char_signal = CharSignal('?', data)
        char_signal.set_length(self.training_config.max_input_len)
        return char_signal.get_array()

    def predict_char(self, data: List[List[float]]) -> str:
        assert self._model is not None, "No model created"
        probability_model = tf.keras.Sequential([self._model,
                                                 tf.keras.layers.Softmax()])
        predictions = probability_model.predict(self._prepare_char(data))

        return chr(np.argmax(predictions[0]) + ord('A'))

    def set_training_char_sequence(self,
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

        self.training_sequence = chars
        return len(chars)

    def _next_file_no(self, char) -> int:
        """Returns next unused signal number in dir of data_path."""
        all_files = listdir(self.training_config.training_data_path)
        max_no = -1
        for file in all_files:
            file_no = int(file[1:].split('.')[0])
            if file[0] == char and file_no > max_no:
                max_no = file_no
        return max_no + 1

    def write_to_dataset(self, char_signal: CharSignal) -> None:
        """Saves signal to new file"""
        # char_signal.set_length(self.max_input_len)
        char = char_signal.char
        file_name = self.training_config.training_data_path + \
            str(char) + str(self._next_file_no(char)) + '.csv'
        with open(file_name, mode='w') as data_file:
            data_writer = csv.writer(data_file)
            data_writer.writerows(char_signal.signal)

    def prepare_training_data(self) -> int:
        """Returns number of signal files processed.
        Sets self._train_values, self._train_labels."""
        data = []
        for file_name in listdir(self.training_config.training_data_path):
            assert file_name.endswith('.csv'), "Non-csv file in data directory"
            with open(self.training_config.training_data_path+file_name) as data_file:
                csv_reader = csv.reader(data_file)
                row_list = [[float(x) for x in row] for row in csv_reader]
                char_signal = CharSignal(file_name[0], row_list)
                char_signal.set_length(self.training_config.max_input_len)
                data.append(char_signal)
        shuffle(data)
        self._train_labels = []
        self._train_values = []
        for char_signal in data:
            self._train_labels.append(ord(char_signal.char)-ord('A'))
            self._train_values.append(char_signal.signal)
        self._train_labels = np.array(self._train_labels)
        self._train_values = np.array(self._train_values)
        # not divided by 100 to reduce values to < 1

        return len(data)

    def train(self) -> None:
        assert type(self._train_values) == np.ndarray
        assert type(self._train_labels) == np.ndarray

        self._model = tf.keras.Sequential([
            tf.keras.layers.Flatten(input_shape=(
                self.training_config.max_input_len, 3)),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(4)
        ])
        self._model.compile(optimizer='adam',
                            loss=tf.keras.losses.SparseCategoricalCrossentropy(
                                from_logits=True),
                            metrics=['accuracy'])
        self._model.fit(self._train_values, self._train_labels, epochs=10)


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

        self.training_sequence = None

    def set_training_char_sequence(self,
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

        self.training_sequence = chars
        return len(chars)

    def _next_file_no(self, char) -> int:
        """Returns next unused signal number in dir of data_path."""
        all_files = listdir(self._data_path)
        max_no = -1
        for file in all_files:
            file_no = int(file[1:].split('.')[0])
            if file[0] == char and file_no > max_no:
                max_no = file_no
        return max_no + 1

    def write_to_dataset(self, char_signal: CharSignal) -> None:
        """Saves signal to new file"""
        # char_signal.set_length(self.max_input_len)
        char = char_signal.char
        file_name = self._data_path + \
            str(char) + str(self._next_file_no(char)) + '.csv'
        with open(file_name, mode='w') as data_file:
            data_writer = csv.writer(data_file)
            data_writer.writerows(char_signal.signal)

    def prepare_training_data(self) -> int:
        """Returns number of signal files processed.
        Sets self._train_values, self._train_labels."""
        data = []
        for file_name in listdir(self._data_path):
            assert file_name.endswith('.csv'), "Non-csv file in data directory"
            with open(self._data_path+file_name) as data_file:
                csv_reader = csv.reader(data_file)
                row_list = [[float(x) for x in row] for row in csv_reader]
                char_signal = CharSignal(file_name[0], row_list)
                char_signal.set_length(self.max_input_len)
                data.append(char_signal)
        shuffle(data)
        self._train_labels = []
        self._train_values = []
        for char_signal in data:
            self._train_labels.append(ord(char_signal.char)-ord('A'))
            self._train_values.append(char_signal.signal)
        self._train_labels = np.array(self._train_labels)
        self._train_values = np.array(self._train_values)
        # not divided by 100 to reduce values to < 1

        return len(data)

    def train(self) -> None:
        assert type(self._train_values) == np.ndarray
        assert type(self._train_labels) == np.ndarray

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


def main():
    conn = Remote()
    conn.send_ready_signal()

    train = Training()
    # no_of_chars = train.set_training_char_sequence(
    #     chars=['A', 'B', 'C', 'D'], include_extra_chars=False)

    # print(f'training sequence: {no_of_chars}')

    # for c in train.training_sequence:
    #     print(f'reading char: {c}; remaining: {no_of_chars}')
    #     train.write_to_dataset(conn.receive_char(c))
    #     no_of_chars -= 1

    train.prepare_training_data()
    train.train()


if __name__ == '__main__':
    main()
