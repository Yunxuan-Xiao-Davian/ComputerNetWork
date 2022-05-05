# -*- coding: UTF-8 -*-


from socket import *
import os
import struct
import time
import select
import socket

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
ICMP_UNREACHABLE_TYPE = 3  # ICMP type code for destination host/network unreachable
ICMP_HOST_UNREACHABLE_CODE = 1  # ICMP code for destination host unreachable
ICMP_NETWORK_UNREACHABLE_CODE = 0  # ICMP code for destination network unreachable
ID = 0  # ID of icmp_header
SEQUENCE = 0  # sequence of ping_request_msg


def checksum(str):
    csum = 0
    count_to = (len(str) / 2) * 2
    count = 0
    while count < count_to:
        this_val = str[count + 1] * 256 + str[count]
        csum = csum + this_val
        csum = csum & 0xffffffff
        count = count + 2
    if count_to < len(str):
        csum = csum + str[len(str) - 1].decode()
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receiveOnePing(icmpSocket, ID, timeout):
    time_start = time.time()  # Recode the begin time of receive

    # Try to connect, wait until the socket buffer is larger than one byte, then handle
    what_ready = select.select([icmpSocket], [], [], timeout)
    time_in_recev = time.time() - time_start  # Recode the end time of receive

    if time_in_recev > timeout:  # Overtime
        print('overtime')
        return -0.001

    if not what_ready[0]:  # Fail to connect
        print("none")
        return -0.001
    time_end = time.time()  # Recode the receive time
    rec_packet, addr = icmpSocket.recvfrom(1024)  # receive data
    byte_in_double = struct.calcsize("!d")  # The size of double type
    time_sending = struct.unpack("!d", rec_packet[28: 28 + byte_in_double])[0]
    total_delay = time_end - time_sending

    rec_header = rec_packet[20:28]  # IP[0:20]

    # Unpack the packet header to use information
    reply_type, reply_code, reply_ckecksum, reply_id, reply_sequence = struct.unpack('!bbHHh', rec_header)

    if ID == reply_id and reply_type == ICMP_ECHO_REPLY:  # Check that the ID matches between the request and reply
        return total_delay

    if reply_type == ICMP_UNREACHABLE_TYPE:  # Unachieve

        if reply_code == ICMP_NETWORK_UNREACHABLE_CODE:  # Destination network unreachable
            return -0.002

        elif reply_code == ICMP_HOST_UNREACHABLE_CODE:  # Destination host unreachable
            return -0.003

        else:  # Other errors
            return -0.004


def sendOnePing(Socket, destinationAddress, ID):
    check_sum = 0

    header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, check_sum, ID, SEQUENCE)  # Build ICMP header
    time_send = struct.pack('!d', time.time())

    check_sum = checksum(header + time_send)  # Checksum ICMP packet using given function
    header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, check_sum, ID, SEQUENCE)  # Insert checksum into packet

    packet = header + time_send
    Socket.sendto(packet, (destinationAddress, 80))  # Send packet using socket


def doOnePing(destination_address, timeout):
    # Create ICMP socket
    my_name = socket.getprotobyname('icmp')  # Get ICMP protocol
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, my_name)  # IPv4,UDP
    sendOnePing(my_socket, destination_address, my_ID)  # Call sendOnePing function
    total_delay = receiveOnePing(my_socket, my_ID, timeout)  # Call receiveOnePing function
    my_socket.close()  # Close ICMP socket

    return total_delay


def ping(my_host, time_out, count):
    send = 0  # Successful sending times
    lost = 0  # Failed sending times
    receive = 0  # Times of success
    max_delay = 0  # Maximum delay
    min_delay = 1000  # Minimum delay, default 1000ms
    sum_delay = 0  # Total delay

    des_addr = socket.gethostbyname(my_host)  # Get host address, look up hostname, and resolve it to an IP address
    global my_ID
    my_ID = os.getpid()  # Obtain the process identification code.

    for i in range(0, count):  # run specified times
        global SEQUENCE
        SEQUENCE = i
        delay = doOnePing(des_addr, time_out / 1000) * 1000  # Call doOnePing function
        send += 1
        # If succeed
        if delay > 0:
            receive += 1
            if max_delay < delay:
                max_delay = delay
            if min_delay > delay:
                min_delay = delay
            sum_delay += delay
            # Print out the returned delay
            print("Receive from: " + str(des_addr) + ", delay = " + str(int(delay)) + "ms")
        # Handle exception
        else:
            if delay == -1:
                print("Fail to connect.")
            elif delay == -2:
                print("Error: Destination Network Unreachable")
            elif delay == -3:
                print("Error: Destination Host Unreachable")
            else:
                print("Error: An Unknown Error Happened")
            lost += 1

        time.sleep(1)
    # If all the test failed, then stop the program
    if receive == 0:
        print("All test failed!")
        return
    # calculate average delay
    avg_time = sum_delay / receive
    # calculate rate of success
    recv_rate = receive / send * 100.0
    print("\nTested Address: " + str(my_host))
    print("\nSend: " + str(send) + "\nSuccess: " + str(receive) + "\nLost: " + str(lost) +
          "\nsuccess rate: " + str(recv_rate))
    print("MaxDelay = " + str(int(max_delay)) + "ms, MinDelay = " + str(int(min_delay)) + "ms, AvgDelay = " + str(
        int(avg_time)) + "ms.")


# host you want to access [default site is lancaster.ac.uk]
dest_host = input("Input the IP you want to test[default:lancaster.ac.uk]:\n")
if len(dest_host) == 0:
    dest_host = "lancaster.ac.uk"
# measuring the arrival time [default is 4 times]
count = input("Please set the counting times[default 4]:\n")
if len(count) == 0:
    count = 4
# set the time out [default timeout is 1s]
timeout = input("Please set the timeout(unit: ms)[default 1000ms]:\n")
if len(timeout) == 0:
    timeout = 1000

ping(dest_host, int(timeout), int(count))
