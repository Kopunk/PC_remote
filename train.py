#!/bin/python3
from connect import ConnectRemote

if __name__ == "__main__":
    conn = ConnectRemote()
    conn.train(30, ["A", "B", "C", "D"])
