# -*- coding: UTF-8 -*-
import os
import urllib
import webbrowser
from socket import *
# Build a client socket 建立客户端的套接字
client_socket = socket(AF_INET, SOCK_STREAM)
# Build a connection to server
client_socket.connect(("127.0.0.1", 8000))

while True:
    # Input the object filename
    obj = input("Hello, which document do you want to query?(for exampel: Lancaster_University.html)")
    if len(obj) == 0:
        obj="Lancaster_University.html"
    # Write the GET header
    Head = 'Get ' + obj + " HTTP/1.1\r\nHost: localhost:10000\r\nConnection: close\r\nUser-agent: Mozilla/5.0\r\n\r\n"
    # Send request using socket
    client_socket.send(Head.encode('utf-8'))
    # Get the message
    recv_data = client_socket.recv(1024*1000).decode('utf-8')
    write_data = recv_data.splitlines()[4:]

    file_name = "./recv_index.html"  # the path of the file placed
    f = open(file_name, 'wb')
    # read the contex in the file as binary format
    for lines in write_data:
        f.write(lines.encode())
        f.write("\n".encode())
    f.close()
    file_path = os.path.abspath(file_name)
    print("html file request is stored in " + file_path)
    webbrowser.open_new_tab(file_path)

