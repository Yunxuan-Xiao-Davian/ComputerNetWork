# -*- coding: UTF-8 -*-
'''
addictional work achieved
Addition1 : Binding the Web Server to a configurable port, defined as an optional argument
Addition2 : When a requested file is not available on the server, return a response with the status code Not Found (404)
Addition3 : Create a multithreaded server implementation, capable of handling multiple concurrent connections
Addition4 : implement a Client Server
'''

import socket
import threading  # import thread module


def handleRequest(tcpSocket):
    # 1. Receive request message from the client on connection socket
    print('Waiting for connection:')

    try:
        # receive http request and decode
        data = tcpSocket.recv(2048).decode()
        print(data)

        # extract the request document from http get message
        filename = data.split()[1].replace("/", "")
        print("file name " + filename)

        # 3. Read file according to the request
        f = open(filename, 'rb')  # open(path+file name, read-write mode, encoding) f =\index.html
        # Read size bytes from the current position of the file.
        # If there is no parameter size, it means that it is read until the end of the file,
        #  and its range is a string object
        content = f.read().decode()
        f.close()
        # 5. Send the HTTP response message
        res_header = 'HTTP/1.1 200 OK\r\n\r\n'
        tcpSocket.send((res_header + content).encode())

    # if there have input/output errors, excute except

    except IOError:
        res_header = 'HTTP/1.1 404 NOT FOUND\r\n\r\n'  # \r\n\r\n
        # 6. Send the content of the file to the socket
        tcpSocket.send(res_header.encode())
        print(res_header)
        # 7. Close the connection socket
        tcpSocket.close()


def startServer(server_address, server_port):
    # tcp protocal
    TCP = socket.getprotobyname('tcp')
    '''
    1. create server socket
    '''
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, TCP)  # (IPV4，TCP)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    '''
    2. Bind the socket to the server ip address and port
    '''
    print("Ready to server...")
    server_socket.bind((server_address, int(server_port)))  # Address/Port number
    '''
    3. Continuously listen for connections to server socket
    This line allows the server to listen to TCP connection requests from clients.
    parameter of the listen() function represents the maximum number of connections (at least 1)
    '''
    server_socket.listen(128)
    '''
    4. When a connection is accepted, call handleRequest function, passing new connection socket (see https://docs.python.org/3/library/socket.html#socket.socket.accept)
    clients apply for connection
    accept() function for the server socket,
    creates connection_socket which represents connection,
    only represents the connection of the server and the specific connection.
    '''
    while True:
        try:
            connection_socket, client_addr = server_socket.accept()
            thread = threading.Thread(target=handleRequest, args=(connection_socket,))
            print("one connection is established, ", end="")
            print("address is: %s" % str(client_addr))
            thread.start()  # Execute child thread
        except Exception as err:
            print(err)
            break
    '''
    5. Close server socket
    '''
    server_socket.close()


if __name__ == "__main__":

    server_address = ""
    server_port = input("enter the port number: [default:8000]")
    if len(server_port) == 0:
        server_port = 8000

    startServer(server_address, server_port)
