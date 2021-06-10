#!/bin/python3

from connect import ConnectRemote
from time import time, sleep
from random import shuffle

import socket
import csv
from os import path, listdir, mkdir
from typing import Union, List, Tuple

import numpy as np
from numpy.core.defchararray import array
import tensorflow as tf
from tensorflow.python.distribute import parameter_server_strategy

from pynput.mouse import Controller as MouseController
from pynput.mouse import Button
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key

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
            print(type(self.signal))
            self.signal += [[.0, .0, .0] for _ in range(len_diff)]

    def get_array(self) -> np.ndarray:
        ret_array = np.array(self.signal)
        # ret_array = np.ravel(ret_array)  # not necessary
        return ret_array


@dataclass
class SensorConfig:
    mode: str = 'gyro'
    accel_multiplier: float = 2.5
    accel_treshold: float = .7
    gyro_multiplier: float = 8
    gyro_treshold: float = .1
    double_click_time = .3
    button_hold_time: float = .3
    hybrid_switch_treshold = 2


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

    COMM_MSG = {
        'end': 'main_release',
        'spec': 'secondary_press',
        'rel': 'secondary_release',

        'main_release': 'end',
        'secondary_press': 'spec',
        'secondary_release': 'rel',
    }

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

        self.available_chars: tuple
        self.enable_verbose = True

    def _verbose(self, s) -> None:
        if self.enable_verbose:
            print(s)

    def send_ready_signal(self) -> None:
        self._s.sendto(bytes(1), self.conn_config.remote_addr)

    def receive_data(self) -> Union[Tuple[List[float], List[float]], str]:
        data, _ = self._s.recvfrom(256)
        data = data.decode()

        assert data.startswith(':'), "Unexpected data recieved"
        data = data[1:]

        if data in self.COMM_MSG.keys():
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
            elif data == self.COMM_MSG['main_release']:
                break

        return CharSignal(char, data_list)

    def cursor(self) -> None:
        """Double click main button to exit cursor.
        Press and hold secondary button to right click."""
        virtual_mouse = MouseController()

        hold_timer = 0
        start_hold_timer = True
        double_click_timer = 0
        data = self.receive_data()
        while True:
            data = self.receive_data()
            if type(data) == str:
                if self.COMM_MSG[data] == 'secondary_press':
                    if start_hold_timer:
                        hold_timer = time()
                        start_hold_timer = False
                    if time() - hold_timer >= self.sensor_config.button_hold_time:
                        virtual_mouse.click(Button.right)
                        start_hold_timer = True
                        sleep(.8)
                elif self.COMM_MSG[data] == 'secondary_release':
                    start_hold_timer = True
                    virtual_mouse.click(Button.left)
                elif self.COMM_MSG[data] == 'main_release':
                    if time() - double_click_timer < self.sensor_config.double_click_time:
                        break
                    double_click_timer = time()
                continue

            if 'gyro' in self.sensor_config.mode:
                data = data[1]
                if abs(data[2]) > self.sensor_config.gyro_treshold:
                    virtual_mouse.move(- int(data[2] *
                                             self.sensor_config.gyro_multiplier), 0)
                if abs(data[0]) > self.sensor_config.gyro_treshold:
                    virtual_mouse.move(
                        0, - int(data[0]*self.sensor_config.gyro_multiplier))

            elif 'hybrid' in self.sensor_config.mode:
                # data = data
                if abs(data[1][2]) > self.sensor_config.gyro_treshold:
                    virtual_mouse.move(
                        - int(data[1][2] * self.sensor_config.gyro_multiplier), 0)
                elif abs(data[0][0]) > self.sensor_config.accel_treshold and \
                        abs(data[0][0]) < self.sensor_config.hybrid_switch_treshold:
                    virtual_mouse.move(- int(data[0][0]), 0)

                if abs(data[1][0]) > self.sensor_config.gyro_treshold:
                    virtual_mouse.move(
                        0, - int(data[1][0]*self.sensor_config.gyro_multiplier))
                elif abs(data[0][1]) > self.sensor_config.accel_treshold and \
                        abs(data[0][1]) < self.sensor_config.hybrid_switch_treshold:
                    virtual_mouse.move(0, - int(data[0][1]))

            else:  # deafults to mode == accel
                data = data[0]
                if abs(data[0]) > self.sensor_config.accel_treshold:
                    virtual_mouse.move(- int(data[0]) *
                                       self.sensor_config.accel_multiplier, 0)
                if abs(data[1]) > self.sensor_config.accel_treshold:
                    virtual_mouse.move(0, - int(data[1]) *
                                       self.sensor_config.accel_multiplier)

    def keyboard(self) -> None:
        virtual_keyboard = KeyboardController()
        no_of_data = self.prepare_training_data()
        self._verbose(f'number of signals in training set: {no_of_data}')
        self.train()

        char_signal = self.receive_char('?')
        self._verbose('received signal')
        char = self.predict_char(char_signal.signal)  # BAC
        self._verbose(f'predicted character: {char}')
        virtual_keyboard.press(char)
        virtual_keyboard.release(char)

    def _prepare_char(self, data) -> np.ndarray:
        char_signal = CharSignal('?', data)
        char_signal.set_length(self.training_config.max_input_len)
        return char_signal.get_array()

    def predict_char(self, data: List[List[float]]) -> str:
        assert self._model is not None, "No model created"
        probability_model = tf.keras.Sequential([self._model,
                                                 tf.keras.layers.Softmax()])
        # self._verbose(self._prepare_char(data))
        prediction = probability_model.predict(
            np.array([self._prepare_char(data)]))

        return self.available_chars[np.argmax(prediction)]

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
        self.available_chars = tuple(
            set(char_signal.char for char_signal in data))
        shuffle(data)
        self._train_labels = []
        self._train_values = []
        for char_signal in data:
            self._train_labels.append(
                self.available_chars.index(char_signal.char))
            self._train_values.append(char_signal.get_array())
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


def main():
    r = Remote(SensorConfig(), ConnectionConfig(), TrainingConfig())
    r.send_ready_signal()
    r.keyboard()


if __name__ == '__main__':
    main()
