#!/bin/python3

import socket
import csv
from time import time, sleep

from pynput.mouse import Controller, Button

class ConnectRemote:
    END_MSG = "end"
    SPECIAL_MSG = "spec"

    def __init__(self):
        self.remote_ip = "192.168.1.230"
        self.remote_port = 2999
        self.remote_addr = (self.remote_ip, self.remote_port)

        self.server_ip = "192.168.1.100"
        self.server_port = 3999
        self.server_addr = (self.server_ip, self.server_port)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(self.server_addr)
        self.s.sendto(bytes(1), self.remote_addr)  # send simple data to enable remote

    # def receive(self):
    #     """Contents of previous 'conntest.py'"""
    #     data, addr = self.s.recvfrom(4092)
    #     x = data.decode()

    #     assert x.startswith(":"), "Unexpected data recieved"
    #     x = x[1:]

    #     x = x.split(":")
    #     x = [float(x_) for x_ in x]
    #     acc, gyro = x[:3], x[3:]

    #     # c += 1

    #     # if c >= 500:  # ~250 readings / s
    #     #     print(f"500 packages in {time()-t} s")  
    #     #     c = 0
    #     #     t = time()
    #     print(f"acc: {acc[0]}\t{acc[1]}\t{acc[2]}") 

    def data_receive_decode(self):
        data, addr = self.s.recvfrom(4092)
        x = data.decode()

        assert x.startswith(":"), "Unexpected data recieved"
        x = x[1:]

        if x == ConnectRemote.END_MSG:
            return False
        elif x == ConnectRemote.SPECIAL_MSG:
            return True
        
        x = x.split(":")
        x = [float(x_) for x_ in x]
        acc, gyro = x[:3], x[3:]

        return acc, gyro
    
    def train(self, repeat: int = 20, chars: list = []):
        if chars == []:
            chars = [chr(i) for i in range(ord("A"), ord("Z")+1)]

        for c in chars:
            print(f"Now reading '{c}' gesture.")
            for i in range(repeat):
                with open(f"train_char/{c}{i}.csv", mode="w") as data_file:
                    data_writer = csv.writer(data_file, delimiter=",")
                    print(f"{c} {i}")
                    
                    data = self.data_receive_decode()
                    while data != False:
                        if data == True:
                            break
                        data_writer.writerow(data[0])
                        data = self.data_receive_decode()

    def cursor(self, mode: str = "gyro"):
        mouse = Controller()

        print(f"'{mode}' mode. Press main button to enable cursor movement")
        while(not (self.data_receive_decode() == False)): continue

        print("Cursor control while pressing main. Double-click main to quit.")

        accel_multiplier = 2.5
        accel_treshold = .7
        gyro_multiplier = 8
        gyro_treshold = .1
        counter = None

        while(True):
            data = self.data_receive_decode()
            if data == True:
                mouse.click(Button.left)
                while(self.data_receive_decode() == True): continue
                continue
            if data == False:
                if counter == None:
                    counter = time()
                elif time() - counter < .3:
                    break
                counter = time()
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
            
