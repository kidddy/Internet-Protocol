#!/usr/bin/python3

import sys
import os
import logging
import socket
import time
import datetime
import struct
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor


_system_epoch = datetime.date(*time.gmtime(0)[0:3])
_sntp_epoch = datetime.date(1900, 1, 1)
TIME_SINCE_1900 = (_system_epoch - _sntp_epoch).days * 24 * 3600

MAX_WORKERS = 3

class ServerSNTP(ThreadPoolExecutor):

    HOST = '0.0.0.0'
    PORT = 8000
    PKT_FORMAT = "!BBBbII4sQQQQ"  # Struct format

    def __init__(self, offset):
        ThreadPoolExecutor.__init__(self, max_workers=MAX_WORKERS)
        self._offset = offset
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
            socket.getprotobyname("UDP"))
        logging.debug("Server initialized")

    def start(self):
        self._sock.bind((ServerSNTP.HOST, ServerSNTP.PORT))
        while True:
            query_data, dest = self._sock.recvfrom(1024)
            logging.info("Query received")
            answer = self.create_answer(query_data)
            self.submit(self._send_answer, answer, dest)

    def create_answer(self, query_data):
        current_time = self.time
        try:
            data = struct.unpack(ServerSNTP.PKT_FORMAT, query_data)
            LI_VN_MODE = 0b11100100  # Leap Indicator: alarm condition, Version Number: 4, Mode: server
            stratum = 2
            poll, precision, root_delay, root_dispersion = 4, 0, 0, 0
            reference_identifier = b"LOCL"
            reference_timestamp = 0
            originate_timestamp = data[10]
            receive_timestamp = current_time
            transmit_timestamp = self.time
            answer = struct.pack(ServerSNTP.PKT_FORMAT,
                LI_VN_MODE, stratum, poll, precision,
                root_delay,
                root_dispersion,
                reference_identifier,
                reference_timestamp,
                originate_timestamp,
                receive_timestamp,
                transmit_timestamp)
            return answer
        except struct.error:
            logging.info("Bad packet received")
        return b''

    def _send_answer(self, data, dest):
        self._sock.sendto(data, dest)

    @property
    def time(self):
        return int(time.time() + TIME_SINCE_1900 + self._offset) * 2**32

    def shutdown(self, wait=True):
        logging.debug("Shutting down")
        self._sock.close()
        ThreadPoolExecutor.shutdown(self, wait)


def parse_args(args):
    parser = ArgumentParser(description="Sntp server")
    parser.add_argument("-l", "--log-level", action='store', dest="log_lvl",
                        default="CRITICAL",
                        help="Logging level. Should be one of: CRITICAL,"
                        "ERROR, WARNING, INFO, DEBUG.")
    #  if len(args) == 0:
        #  print("Arguments not found")
        #  parser.print_help()
        #  return None
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    if args is None:
        sys.exit(1)
    logging.basicConfig(level=args.log_lvl)
    server = None
    config_file = "config.cfg"
    if config_file not in os.listdir():
        print(f"{config_file} doesn't exists")
        sys.exit(1)
    with open(config_file, mode='r') as f:
        offset = int(f.readline().rstrip("\n"))
    try:
        server = ServerSNTP(offset)
        server.start()
    except KeyboardInterrupt:
        logging.warning("Interupted")
        sys.exit(0)
    except Exception as e:
        logging.exception(e)
        sys.exit(2)
    finally:
        if server:
            server.shutdown()


if __name__=="__main__":
    main()
