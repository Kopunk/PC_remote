#!/bin/python3

import socket
import csv

class ConnectRemote:
    END_MSG = "end"

    def __init__(self):
        self.remote_ip = "192.168.1.230"
        self.remote_port = 2999
        self.remote_addr = (self.remote_ip, self.remote_port)

        self.udp_ip = "192.168.1.100"
        self.udp_port = 3999
        self.server_addr = (self.udp_ip, self.udp_port)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(self.server_addr)
        self.s.sendto(bytes(1), self.remote_addr)  # send simple data to enable remote

    def receive(self):
        """Contents of previous 'conntest.py'"""
        data, addr = self.s.recvfrom(4092)
        x = data.decode()

        assert x.startswith(":"), "Unexpected data recieved"
        x = x[1:]

        x = x.split(":")
        x = [float(x_) for x_ in x]
        acc, gyro = x[:3], x[3:]

        # c += 1

        # if c >= 500:  # ~250 readings / s
        #     print(f"500 packages in {time()-t} s")  
        #     c = 0
        #     t = time()
        print(f"acc: {acc[0]}\t{acc[1]}\t{acc[2]}") 

    def data_receive_decode(self):
        data, addr = self.s.recvfrom(4092)
        x = data.decode()

        assert x.startswith(":"), "Unexpected data recieved"
        x = x[1:]

        if x == ConnectRemote.END_MSG:
            return False
        
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
                        data_writer.writerow(data[0])
                        data = self.data_receive_decode()


