
import socket
import ssl
import argparse
import sys
import re
import getpass
import traceback

from email.header import decode_header


EOL = "\r\n"

ANSWER_PATTERN = re.compile(r"([-+]OK|ERR)\s+(.*)")

def read_bytes(sock):
    data = b""
    while True:
        try:
            part = sock.recv(512)
            if not part:
                break
            data += part
        except socket.timeout:
            break
    return data

 
def read_text(sock, encoding="UTF-8"):
    return read_bytes(sock).decode(encoding).rstrip()


def send_text(sock, text, encoding="UTF-8"):
    sock.send((text + EOL).encode(encoding))

 
def parse_answer(text):
    lines = text.split(EOL)
    answer = lines[0]
    data_lines = [] if len(lines) == 1 else lines[1:]
    match = ANSWER_PATTERN.match(answer)
    status_indicator = "-ERR"
    answer_msg = ""
    if match:
        status_indicator = match.group(1)
        answer_msg = match.group(2)
    return (status_indicator, answer_msg), data_lines


def get_and_parse(ssl_sock, encoding="UTF-8"):
    answ = read_text(ssl_sock, encoding)
    return parse_answer(answ)


def send_and_get(ssl_sock, text, encoding="UTF-8"):
    send_text(ssl_sock, text, encoding)
    return get_and_parse(ssl_sock, encoding)


def die(msg="Protocol error"):
    print(msg)
    sys.exit(1)


SERVER_NAME = "server"

def print_answ(status, msg, data=None):
    print(SERVER_NAME + ": " + f"{status} {msg}")
    if data: [print("\t" + line) for line in data]

def get_raw_mail(sock, mail_num) -> str:
    req = f"RETR {mail_num}"
    print("Client: " + req)
    status_and_msg, data = send_and_get(sock, req)
    print_answ(*status_and_msg)
    return EOL.join(line for line in data)

def get_raw_top_mail(sock, mail_num, num_lines=0):
    req = f"TOP {mail_num} {num_lines}"
    print("Client: " + req)
    status_and_msg, data = send_and_get(sock, req)
    print_answ(*status_and_msg)
    return EOL.join(line for line in data)

def get_mail(sock, mail_num):
    mail = get_raw_mail(sock, mail_num)
    m = RE_SEP_HEADER.match(mail)
    head = m.group(1)
    text = m.group(2)
    return head, text


RE_SEP_HEADER = re.compile(r"(.*?)\s*\n\W*\n\s*(.*)\n\.", re.MULTILINE | re.DOTALL)
RE_SUBJECT = re.compile(r"Subject:\s(.*)", re.MULTILINE)
RE_DATE = re.compile(r"Date:\s(.*)", re.MULTILINE)
RE_FROM = re.compile(r"From:\s(.*(?:\n\s+.*)?)", re.MULTILINE)
RE_EMAIL = re.compile(r"(\w+@\w+\.\w+)")
RE_TO = re.compile(r"To: (.*)", re.MULTILINE)

def convert(data):
    bs, enc = decode_header(data)[0]
    return bs.decode(enc) if enc else bs

def parse_mail_head(mail_head: str):
    m_subject = RE_SUBJECT.search(mail_head)
    m_date = RE_DATE.search(mail_head)

    m_from = RE_FROM.search(mail_head)
    email = RE_EMAIL.search(m_from.group(1))
    email = email.group(1) if email else m_from.group(1)

    m_to = RE_TO.search(mail_head)

    subject = m_subject.group(1) if m_subject else "(no subject)"
    subject = convert(subject)

    return (subject,
            m_date.group(1) if m_date else "(no date)",
            email,
            m_to.group(1) if m_to else "(no destination e-mail)")

# - - - - - - - - - - - - - - - INTERACTIVE MODE COMMANDS
# def abstract_cmd(sock, *args) => None

def list_cmd(sock, *args):
    status_and_msg, data = send_and_get(sock, "LIST")
    for line in data:
        if line == ".": break
        mail_idx = int(line.split(" ")[0])
        if mail_idx == ".": break
        head, _ = get_mail(sock, mail_idx)
        subject, date, sender, receiver = parse_mail_head(head)
        print("{}) {}".format(mail_idx, date))
        print("\tSubject: " + subject)
        print("\tfrom: " + sender)
        print("\tto: " + receiver)
        print()

def quit_cmd(sock, *args):
    status_and_msg, data = send_and_get(sock, "QUIT")
    print_answ(*status_and_msg, data)
    sock.close()
    die("Closing client")


def retr_cmd(sock, mail_num, *args):
    head, text = get_mail(sock, mail_num)
    subject, date, sender, receiver = parse_mail_head(head)
    print()
    print("\tSubject: " + subject)
    print("\tDate: " + date)
    print("\tfrom: " + sender)
    print("\tto: " + receiver)
    print()
    print(text)

def top_cmd(sock, mail_num, num_lines=0, *args):
    mail = get_raw_top_mail(sock, mail_num, num_lines)
    if num_lines==0:
        head = mail
        text = ""
    else:
        m = RE_SEP_HEADER.match(mail)
        head = m.group(1)
        text = m.group(2)
    subject, date, sender, receiver = parse_mail_head(head)
    print()
    print("\tSubject: " + subject)
    print("\tDate: " + date)
    print("\tfrom: " + sender)
    print("\tto: " + receiver)
    (print(), print(text)) if text else None
    

COMMANDS = dict()
COMMANDS["LIST"] = list_cmd
COMMANDS["QUIT"] = quit_cmd
COMMANDS["RETR"] = retr_cmd
COMMANDS["TOP"] = top_cmd


def interactive_mode(sock, server_name="server"):
    print("Interactive mode:")
    SERVER_NAME = server_name
    while True:
        try:
            cmd = input("--> ")
            if cmd[0] == "!":
                cmd = cmd[1:]
                status_and_msg, data = send_and_get(sock, cmd)
                print_answ(*status_and_msg, data)
            else:
                cmd, *args = cmd.split(" ")
                cmd = cmd.upper()
                COMMANDS[cmd](sock, *args)
        except Exception:
            print(traceback.format_exc())
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def connect(dest):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = ssl.wrap_socket(s)
        ssl_sock.settimeout(1)
        ssl_sock.connect(dest)

        (status, msg), _ = get_and_parse(ssl_sock)
        if status != "+OK": die()
        print(f"Connected to {dest[0]}")

        login, passwd = get_login_passwd()

        (status, msg), _ = send_and_get(ssl_sock, "USER " + login)
        if status != "+OK": die("Wrong login")
        print("Login OK")

        (status, msg), _ = send_and_get(ssl_sock, "PASS " + passwd)
        if status != "+OK": die("Wrong password")
        print("Password OK")

        # (status, msg), messages = send_and_get(ssl_sock, "LIST")
        # if status != "+OK": print("Protocol error: LIST request")
        # else:
            # messages_num, summ_size = msg.split(" ")
            # print(f"{messages_num} messages. Total {summ_size} bytes.")
            # for line in messages:
                # if line == ".": continue
                # msg_id, size = line.split(" ")
                # print(f"Message #{msg_id}: {size} bytes")

        interactive_mode(ssl_sock, dest[0])
        

    except socket.timeout:
        die("Server doesn't respond")
    finally:
        s.close()


def get_login_passwd():
    login = input("LOGIN: ")
    passwd = getpass.getpass("PASSWORD: ")
    return login, passwd


def init_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("server", action="store")
    parser.add_argument("-p", "--port", type=int, action="store", default=110)
    return parser


def main():
    parser = init_parser()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args(sys.argv[1:])
    connect((args.server, args.port))
    


if __name__ == "__main__":
    main()
