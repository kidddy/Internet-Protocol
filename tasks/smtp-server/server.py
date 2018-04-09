#!/usr/bin/python3


import socket
import sys
import ssl
import base64
from xxd import Dumper


PORT = 465
dumper = Dumper()
ENCODING = "utf-8"

with open("gentoo.jpg", "rb") as f:
    image = base64.b64encode(f.read())

def create_msg():
    string = b"""From: Larry the Cow
To: qxid@yandex.ru
Subject: SuperTestMsg1IMAGE
MIME-Version: 1.0
Content-Type: multipart/mixed;
	boundary="bound.gnu_bound"

--bound.gnu_bound
Content-Type: text/plain;

If it moves, compile it.
--bound.gnu_bound
Content-Disposition: attachment; filename="gentoo.jpg"
Content-Transfer-Encoding: base64
Content-Type: image/jpeg; name="gentoo.jpg"

""" + image + b"\n--bound.gnu_bound--\n."
    return string


def send_recv(string, sock):
    string += b"\n"
    sock.send(string)
    return sock.recv(1024)


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s = ssl.SSLSocket(s)
    login = base64.b64encode(b"qxid@yandex.ru")
    password = base64.b64encode(b"17fedfd7")
    try:
        s.connect(("smtp.yandex.ru", PORT))
        data = s.recv(1024)
        for line in dumper(data):
            print(line)
        msg = send_recv(b"EHLO google.ru", s)
        print(msg.decode(ENCODING))
        msg = send_recv(b"AUTH LOGIN", s)
        print(msg.decode(ENCODING))
        msg = send_recv(login, s)
        print(msg.decode(ENCODING))
        msg = send_recv(password, s)
        print(msg.decode(ENCODING))
        msg = send_recv(b"MAIL FROM:qxid@yandex.ru", s)
        print(msg.decode(ENCODING))
        msg = send_recv(b"RCPT TO:qxid@yandex.ru", s)
        print(msg.decode(ENCODING))
        msg = send_recv(b"DATA", s)
        print(msg.decode(ENCODING))
        msg = send_recv(create_msg(), s)
        print(msg.decode(ENCODING))
    except socket.timeout as e:
        print("Server doesn't respond")
    finally:
        s.close()


if __name__ == "__main__":
    main()
