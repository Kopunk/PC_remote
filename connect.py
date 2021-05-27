#!/bin/python3

import socket
import csv
from time import time, sleep
import numpy as np
import tensorflow as tf


from pynput.mouse import Controller, Button


class ConnectRemote:
    MAIN_RELEASE_MSG = "end"
    SEC_PRESS_MSG = "spec"
    SEC_RELEASE_MSG = "rel"

    def __init__(self):
        self.remote_ip = "192.168.1.230"
        self.remote_port = 2999
        self.remote_addr = (self.remote_ip, self.remote_port)

        self.server_ip = "192.168.1.100"
        self.server_port = 3999
        self.server_addr = (self.server_ip, self.server_port)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(self.server_addr)
        # send simple data to enable remote
        self.s.sendto(bytes(1), self.remote_addr)

    def data_receive_decode(self):
        data, addr = self.s.recvfrom(4092)
        x = data.decode()

        assert x.startswith(":"), "Unexpected data recieved"
        x = x[1:]

        if x == ConnectRemote.MAIN_RELEASE_MSG:
            return "main_rel"
        elif x == ConnectRemote.SEC_PRESS_MSG:
            return "sec_press"
        elif x == ConnectRemote.SEC_RELEASE_MSG:
            return "sec_rel"

        x = x.split(":")
        x = [float(x_) for x_ in x]
        acc, gyro = x[:3], x[3:]

        return acc, gyro

    def train_input_train_data(self, repeat: int = 20, chars: list = []):
        if chars == []:
            chars = [chr(i) for i in range(ord("A"), ord("Z")+1)]

        for c in chars:
            print(f"Now reading '{c}' gesture.")
            for i in range(repeat):
                with open(f"train_char/{c}{i}.csv", mode="w") as data_file:
                    data_writer = csv.writer(data_file, delimiter=",")
                    print(f"{c} {i}")

                    data = self.data_receive_decode()
                    while data != "main_rel":
                        if data == "sec_press":
                            break
                        data_writer.writerow(data[0])
                        data = self.data_receive_decode()

    def train_prepare_data(self, sample_data=False):
        class_names = []
        train = []
        train_labels = []

        if sample_data:
            max_line_count = 0
            for c in "ABCD":
                for i in range(30):
                    with open(f"train_char/{c}{i}.csv") as data_file:
                        csv_reader = csv.reader(data_file)
                        row_sum = sum(1 for row in csv_reader)
                        if row_sum > max_line_count:
                            max_line_count = row_sum
                    with open(f"train_char/{c}{i}.csv") as data_file:
                        csv_reader = csv.reader(data_file)
                        row_array = [[float(x) for x in row]
                                     for row in csv_reader]
                    class_names.append(c)
                    train.append(row_array)
        for i in range(len(train)):
            for j in range(max_line_count - len(train[i])):
                train[i].append([0, 0, 0])

        train_labels = [ord(c)-ord('A') for c in class_names]

        train_labels = np.array(train_labels)
        train = np.array(train)
        return train_labels, train

    def train_train_from_data(self, train_labels, train):
        # temp solution to make data ranged < 1
        train = train / 100

        model = tf.keras.Sequential([
            tf.keras.layers.Flatten(input_shape=(365, 3)),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(4)
        ])
        model.compile(optimizer='adam',
            loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            metrics=['accuracy'])
        model.fit(train, train_labels, epochs=10)

    def cursor(self, mode: str = "gyro"):
        mouse = Controller()

        print(f"'{mode}' mode. Press main button to enable cursor movement")
        while(self.data_receive_decode() != "main_rel"):
            continue

        print("Cursor control while pressing main. Double-click main to quit.")

        accel_multiplier = 2.5
        accel_treshold = .7
        gyro_multiplier = 8
        gyro_treshold = .1
        counter_main = time()  # time of last release
        double_click_time = .3

        while(True):
            data = self.data_receive_decode()
            if data == "sec_press":
                continue
            if data == "sec_rel":
                mouse.click(Button.left)
                print("single click")
                continue
            if data == "main_rel":
                if time() - counter_main < double_click_time:
                    print("exit")
                    break
                counter_main = time()
                continue

            if mode == "gyro":
                data = data[1]
                if abs(data[2]) > gyro_treshold:
                    mouse.move(- int(data[2]*gyro_multiplier), 0)
                if abs(data[0]) > gyro_treshold:
                    mouse.move(0, - int(data[0]*gyro_multiplier))

            elif mode == "hybrid":
                # data = data
                if abs(data[1][2]) > gyro_treshold:
                    mouse.move(- int(data[1][2]*gyro_multiplier), 0)
                elif abs(data[0][0]) > accel_treshold and abs(data[0][0]) < 2:
                    mouse.move(- int(data[0][0]), 0)

                if abs(data[1][0]) > gyro_treshold:
                    mouse.move(0, - int(data[1][0]*gyro_multiplier))
                elif abs(data[0][1]) > accel_treshold and abs(data[0][1]) < 2:
                    mouse.move(0, - int(data[0][1]))

            else:  # mode == accel
                data = data[0]
                if abs(data[0]) > accel_treshold:
                    mouse.move(- int(data[0]) * accel_multiplier, 0)
                if abs(data[1]) > accel_treshold:
                    mouse.move(0, - int(data[1]) * accel_multiplier)


if __name__ == "__main__":
    test = ConnectRemote()
    train_labels, train = test.train_prepare_data(True)
    test.train_train_from_data(train_labels, train)
