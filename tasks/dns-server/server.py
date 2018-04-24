#!/usr/local/bin/python3

import sys
import argparse
import time
import protocol
import cache
import resolver
import socket
from itertools import chain
from concurrent.futures import ThreadPoolExecutor


MAX_THREADS = 5


class Server:

    HOST = "127.0.0.1"
    PORT = 53

    def __init__(self, ns_server="8.8.8.8"):
        self._ns_server = ns_server

        cache_A = cache.Cache()
        cache_NS = cache.Cache()
        cache_ERROR = cache.Cache()
        self._cache = {protocol.Question.QTYPE_A: cache_A,
                       protocol.Question.QTYPE_NS: cache_NS,
                       "error": cache_ERROR}

        self._sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self._sock.bind((Server.HOST, Server.PORT))
        #  self._thread_pool = ThreadPoolExecutor(max_workers=MAX_THREADS)

    def freshing_cache(self):
        while True:
            time.sleep(60)
            for cache in self._cache.values():
                cache.refresh()

    def start(self):
        #  self._thread_pool.submit(self.freshing_cache)
        while True:
            query, dest = self._sock.recvfrom(512)
            #  self._thread_pool.submit(self._resolve, query, dest)
            self._resolve(query, dest)

    def _resolve(self, query: bytes, dest_addr):
        pp = protocol.PackageParser(query)
        query_pkg = pp.parsePackage()

        pb_res = protocol.PackageBuilder(query_pkg.identification)
        for question in query_pkg.questions:
            qtype = question.type
            domain_name = question.domain_name
            pb_res.add_question(domain_name, qtype)

            respond = self.get_from_cache(domain_name, qtype)
            if respond is None: continue
            if respond:
                for rdata, ttl in respond:
                    pb_res.add_answer(domain_name, qtype, ttl, rdata)
            else:
                try:
                    answ_pkg, _ = resolver.ask_serverok(domain_name, qtype,
                                                        self._ns_server)
                except socket.timeout:
                    continue
                self._update_cache(answ_pkg)
                respond = self.get_from_cache(domain_name, qtype)
                if respond:
                    for rdata, ttl in respond:
                        pb_res.add_answer(domain_name, qtype, ttl, rdata)
        if len(pb_res.answers) == 0:
            pb_res.set_flags(rcode=2)
        data = pb_res.build().encode()
        self._sock.sendto(data, dest_addr)


    def _update_cache(self, pkg):
        if pkg.flags.rcode != protocol.Flags.RCODE_OK:
            for record in pkg.questions:
                cache = self._cache["error"]
                cache.add(record.domain_name, "", time.time() + 30*60)
        for record in chain(pkg.answers, pkg.access_rights, pkg.extra_records):
            key = record.domain_name
            qtype = record.type
            remove_time = time.time() + record.ttl
            rdata = record.rdata
            self._cache[qtype].add(key, rdata, remove_time)

    def get_from_cache(self, domain_name, qtype) -> list:
        res = []
        if self._cache["error"].contains(domain_name):
            return None
        elif self._cache[qtype].contains(domain_name):
            res  = self._cache[qtype].get(domain_name)
        return res


def init_parser():
    parser = argparse.ArgumentParser(description="Caching DNS server")
    parser.add_argument("-s", "--server", action="store", default="8.8.8.8")
    return parser


def main():
    parser = init_parser()
    args = parser.parse_args(sys.argv[1:])
    server = Server(args.server)
    server.start()

if __name__ == "__main__":
    main()
