#!/bin/python3
from pynput.mouse import Button, Controller

from connect import ConnectRemote

if __name__ == "__main__":
    conn = ConnectRemote()

    mouse = Controller()
    for i in range(10):
        mouse.move(5, -5)

    print("Press main button to enable cursor movement")
    while(not (conn.data_receive_decode() == False)): continue
    
    
    print("Cursor control, press secondary button to quit")

    multiplier = 2.5
    sensitivity = 0.6

    while(True):
        data = conn.data_receive_decode()
        if data == True:
            break
        if data == False:
            continue

        data = data[0]
        if abs(data[0]) > sensitivity:
            mouse.move(- int(data[0]) * multiplier, 0)
        if abs(data[1]) > sensitivity:
            mouse.move(0, - int(data[1]) * multiplier)



