from __future__ import print_function

import hashlib
import os
import socket
import sys
import threading

def getHost(request):
    # Gets the host name, port from the request array
    request_array = request.decode('utf-8').split()
    type = request_array[0]
    host = ''
    port = 80
    if (type == 'GET') | (type == 'DELETE') | (type == 'POST'):
        for i in range(len(request_array)):
            if request_array[i] == 'Host:':
                host = request_array[i + 1]
    print("host " + host)
    return socket.gethostbyname(host), port


def getResponse(request):
    while True:
        try:
            # 1. Create socket
            targetSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # (IPv4,TCP)
            # 2.connect the server socket to server address and server port
            targetSocket.connect((getHost(request)))
            # send the request
            targetSocket.sendall(request)
            # Information received
            response = targetSocket.recv(2048)
            print("File is found in the server")
            # Close the connection socket
            targetSocket.close()
            break
        except:
            print("connection timeout")
            continue
    return response


def onKeyboardEvent(event):
    print(event.Key)  # 返回按下的键
    return True


# check if there is chache file
def loadCache(request):
    file_name = request.decode('utf-8').split()[1].split("//")[1].replace('/', '')
    print("fileName: " + file_name)
    file_path = "./" + file_name.split(":")[0].replace('.', '_')
    try:
        file = open(file_path + "./index.html", 'rb')
        print("File is found in proxy server.")
        print("Send, done.")
        return file.read()
    except:
        print("File is not exist.\nSend request to server...")
        try:
            response_msg = getResponse(request)
            # cache
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            cache = open(file_path + "./index.html", 'w')
            cache.writelines(response_msg.decode("UTF-8").replace('\r\n', '\n'))
            cache_list.append(file_path)
            cache.close()
            print("Cache, done.")
        except IOError as msg:
            print(msg)
            sys.exit()
    return response_msg


def handleRequest(serverSocket):
    # 1. Receive request message from the client on connection socket
    connect_socket, client_address = serverSocket.accept()  # return a socket that represents connection
    print("connection established")
    # 2. Extract the path of the requested object from the message (second part of the HTTP header)
    request = connect_socket.recv(2048)
    print(request)
    res = loadCache(request)  # Loads the file which user want to find
    connect_socket.sendall(res)  # Send the correct HTTP response
    connect_socket.close()  # Close the connection socket


def startProxy(host, port):
    # 1. Create server socket
    serverSorcket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 2. Bind the server socket to server address and server port
    serverSorcket.bind((host, port))
    # 3. Continuously listen for connections to server socket
    serverSorcket.listen(0)
    print("Start Server", port, sep=' ')

    try:
        while True:
            # 4. When a connection is accepted, call handleRequest function, passing new connection socket
            handleRequest(serverSorcket)
    except KeyboardInterrupt:
        print('Server Cloced')
        # 5. Close server socket
        serverSorcket.close()
        sys.exit()





if __name__ == '__main__':
    # 1. set http_proxy=http://host:port to start proxy (for example: set http_proxy=http://127.0.0.1:8000)
    # 2. curl to access web by http protocol (for example: curl lancaster.ac.uk)

    global cache_list
    cache_list = []
    port = input("Please input port number[default 8000]:\n")
    if len(port) == 0:
        port = 8000
    thread1 = threading.Thread(target=startProxy, args=('', int(port),))
    thread1.daemon = 1
    thread1.start()
    while True:
        #enter P to shut the proxy and remove cache files
        shut_input = input("enter P to shut\n")
        if shut_input == 'P':
            for i in cache_list:
                filelist = os.listdir(i)
                for file in filelist:
                    os.remove(i+"/"+file)
                os.rmdir(i)
            break

