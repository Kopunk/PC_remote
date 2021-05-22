#!/bin/python3

import socket
from time import time

REMOTE_IP = "192.168.1.230"
REMOTE_PORT = 2999
remote_addr = (REMOTE_IP, REMOTE_PORT)

UDP_IP = "192.168.1.100"
UDP_PORT = 3999
server_addr = (UDP_IP, UDP_PORT)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

s.bind(server_addr)

s.sendto(bytes(1), remote_addr)

# c = 0
# t = time()
while True:
    data, addr = s.recvfrom(4092)
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
