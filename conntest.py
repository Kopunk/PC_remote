#!/bin/python3

import socket

UDP_IP = "192.168.1.100"
UDP_PORT = 2999

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024)
    print(f"received: {data}")
