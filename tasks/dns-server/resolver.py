
import socket
import hexdump


def send_and_get(pkg: bytes, dns_ip="8.8.8.8", dns_port=53):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.settimeout(5)
    sock.sendto(pkg, (dns_ip, dns_port))
    answ, ns_server = sock.recvfrom(512)
    print("Server: " + str(ns_server))
    return answ
