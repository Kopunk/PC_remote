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

t = time()
c = 0
while True:
    data, addr = s.recvfrom(4092)
    print(data)
