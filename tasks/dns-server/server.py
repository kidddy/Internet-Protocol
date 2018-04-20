#!/usr/local/bin/python3

import sys
import argparse
import time
import protocol
import cache
import resolver
import logging
from itertools import chain
from concurrent.futures import TreadPoolExecutor


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
        self._thread_pool = ThreadPoolExecutor(max_workers=MAX_THREADS)

    def freshing_cache(self):
        while True:
            time.sleep(60)
            for cache in self._cache.values():
                cache.refresh()

    def start(self):
        self._thread_pool.submit(self.freshing_cache)
        while True:
            query, dest = self._sock.recvfrom(512)
            self._thread_pool.submit(self._resolve, query, dest)

    def _resolve(self, query: bytes, dest_addr):
        pp = protocol.PackageParser(query)
        query_pkg = pp.parsePackage()
        answers = []
        for question in query_pkg.questions:
            qtype = question.qtype
            domain_name = question.domain_name
            respond = self.get_from_cache(domain_name, qtype)
            if respond is None: continue
            if respond:
                answers.extend(respond)
            else:
                answ_pkg = resolver.ask_serverok(domain_name, qtype, self._ns_server)
                self._update_cache(answ_pkg)
                respond = self.get_from_cache(domain_name, qtype)
                if respond:
                    answers.extend(respond)
        if answers:
            pb = PackageBuilder(query_pkg.identification)

    def _update_cache(self, pkg):
        if pkg.flags.rcode != protocol.Flags.RCODE_OK:
            for record in pkg.questions:
                cache = self._cache["error"]
                cache.add(record.domain_name, "", time.time() + 30*60)
        for record in chain(pkg.answers, pkg.access_rights, pkg.extra_records):
            key = record.domain_name
            qtype = record.qtype
            remove_time = time.time() + record.ttl
            rdata = record.rdata
            self._cache[qtype].add(key, rdata, remove_time)

    def get_from_cache(self, domain_name, qtype) -> list:
        res = []
        if self._cache["error"].contains(domain_name):
            return None
        elif self._cache[qtype].contains(domain_name):
            cached_data = self._cache[qtype].get(domain_name)
            for rdata, ttl in cached_data:
                res.append(protocol.Answer(domain_name, qtype,
                                           protocol.Answer.QCLASS_IN, ttl, rdata))
        return res


def init_parser():
    parser = argparse.ArgumentParser(description="Caching DNS server")
    parser.add_argument("-s", "--server", action="store", default="8.8.8.8")
    return parser


def main():
    parser = init_parser()
    args = parser.parse_args(sys.argv[1:])

if __name__ == "__main__":
    main()
