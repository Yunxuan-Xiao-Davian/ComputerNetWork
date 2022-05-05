# -*- coding: UTF-8 -*-
'''
Completed Additional Tasks:
1. Measuring and reporting packetloss,including unreachable destinations
2. Repeated measurements for each node
3. Configurable timeout, set using an optional argument
4. Configurable protocol (UDP or ICMP), set using an optional argument
5. Resolve the IP addresses found in the responses to their respective hostnames
'''
import socket
import os
import struct
import sys
import time
import select

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
# ICMP overtime
TYPE_ICMP_OVERTIME = 11
CODE_TTL_OVERTIME = 0
# ICMP unreachable
TYPE_ICMP_UNREACHED = 3
addr = None
timeSent = None


def checksum(string):
    # 32 bits decimal number, since when adding 16 bits number it may produce carry. This carry should be rollback
    csum = 0
    countTo = (len(string) / 2) * 2  # count the number of bytes of the string
    count = 0

    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]  # equal to << 8
        csum = csum + thisVal
        csum = csum & 0xffffffff  # save 16 bits overflow
        count = count + 2  # move back two bytes which means sum the next 16 bits

    if count < len(string):
        csum = csum + ord(string[len(string) - 1])
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)  # 32 bits to 16 bits add the overflow number
    csum = csum + (csum >> 16)
    # Take complement
    answer = ~csum
    answer = answer & 0xffff
    # Byte size endthreads transpose. Networks are big endian
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def get_host_name(des_addr):
    try:
        hostname = socket.gethostbyaddr(des_addr)[0]
        IP = des_addr
        return "{0} [{1}]".format(hostname, IP)
    except:
        return des_addr


def receiveOnePing(receive_socket, ID, timeout, prot):
    # time sent addr delay
    time_left = timeout

    while True:
        time_begin = time.time()
        what_ready = select.select([receive_socket], [], [],
                                   time_left)  # Wait until the socket buffer is larger than one byte, then handle the socket
        time_spent = (time.time() - time_begin)
        time_left = time_left - time_spent
        if time_left <= 0:  # Timeout
            return -1
        if not what_ready[0]:
            return -2
        time_received = time.time()
        rec_packet, addr = receive_socket.recvfrom(1024)  # Receive data
        header = rec_packet[20: 28]  # IP:[0: 20]
        acess_type, code, checksum, packetID, sequence = struct.unpack("!bbHHh",
                                                                       header)  # Unpack the packet header for useful information
        if acess_type == 11 or 3 and packetID == ID:  # Check that the ID matches between the request and reply]
            total_delay = time_received - time_begin  # Compare the time of receipt to time of sending, producing the total network delay
            return total_delay, addr[0], acess_type  # Return total network delay information


def sendOnePing(send_socket, destination_address, ID):
    if prot == "ICMP":
        my_checksum = 0
        header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)  # Build ICMP header
        data = struct.pack("!d", time.time())  # Return current time, record the time of sending
        my_checksum = checksum(header + data)  # Checksum ICMP packet
        header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)  # Insert the checksum into packet
        packet = header + data  # Build packet
        send_socket.sendto(packet, (destination_address, 1))  # Send packet using socket,  (hostAddress,port)
    if prot == "UDP":
        msg = struct.pack("!d", time.time())
        length = 8 + len(msg)
        my_checksum = 0
        sport = 7  # arbitrary source port
        dport = 45134  # arbitrary destination port
        udp_header = struct.pack('!HHHH', sport, dport, length, my_checksum)
        my_checksum = checksum(udp_header + msg)
        udp_header = struct.pack('!HHHH', sport, dport, length, my_checksum)
        packet = udp_header + msg
        send_socket.sendto(packet, (destination_address, 1))
        send_socket.close()


def doOneTrace(destinationAddress, timeout, TTL, prot):
    if prot == "ICMP":
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                    socket.getprotobyname('ICMP'))  # Create ICMP socket
        send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, TTL)
        receive_socket = send_socket
    if prot == "UDP":
        # Create UDP socket as send socket
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.getprotobyname('udp'))
        # bind it to port 7 according to the echo protocal
        send_socket.bind(("", 7))
        # Create ICMP socket by echo protocal receive socket is ICMP socket
        receive_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('ICMP'))
        receive_socket.bind(("", 7))
        # Setting options for sockets
        send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, TTL)
        receive_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, TTL)
    sendOnePing(send_socket, destinationAddress, ID)  # Send a ping
    delay = receiveOnePing(receive_socket, ID, timeout, prot)  # Receive a ping
    receive_socket.close()  # Close ICMP socket
    return delay  # Return total network delay


def trace(host, timeout, prot):
    global ID
    ID = os.getpid()  # Identifier(pid)
    TTL = 1
    delay = [0, 0, 0]
    destAdd = socket.gethostbyname(host)  # Look up hostname, resolving it to an IP address
    for i in range(max_hop):
        run_over = False
        addr = None
        loss = 0
        print(str(TTL), end=" ")
        for seq in range(3):  # Transmitted 3 packets
            result = doOneTrace(destAdd, timeout, TTL, prot)
            if result == -1:  # Failed transmitting
                delay[seq] = '*'
                print("*", end=" ")
                loss += 1
            elif result == -2:
                delay[seq] = '*'
                print("*", end=" ")
                loss += 1
            else:  # Successful transmitting
                print(str(int(result[0] * 1000)) + " ms", end=" ")
                addr = result[1]
                if result[2] == 0:
                    run_over = True
            # Print out the returned delay
        if loss == 3:
            print("time out", end=" ")
        else:
            print(get_host_name(addr))
        TTL += 1
        if run_over:
            print("program run over", end=" ")
        if addr == destAdd:
            break
        if i == (max_hop - 1):
            print("exceed max_hop")
            sys.exit()


if __name__ == "__main__":
    global max_hop
    max_hop = 30
    desAddr = input("Please enter the IP or host name[default(www.lancaster.ac.uk)]:\n")
    if len(desAddr) == 0:
        desAddr = 'www.lancaster.ac.uk'

    timeout = input("Please enter the timeout[default:1s]:\n")
    if len(timeout) == 0:
        timeout = 1

    prot = input("Please choose  protocol (UDP or ICMP)[default ICMP]:\n")
    if len(prot) == 0:
        prot = 'ICMP'
    elif prot != 'ICMP' and prot != 'UDP':
        print("Please enter 'ICMP' or 'UDP', default(ICMP)")
    # Start Tracing
    print("Tracing address: " + desAddr + " " + socket.gethostbyname(desAddr))
    print("the max hop is " + str(max_hop))
    trace(desAddr, int(timeout), prot)
