#!/usr/local/bin/python3

import argparse
import sys
import protocol
import resolver


TYPE2INT = {"A": protocol.Question.QTYPE_A,
            "NS": protocol.Question.QTYPE_NS}


def init_argparser():
    parser = argparse.ArgumentParser(description="DNS Client")
    parser.add_argument("domain_name", action="store")
    parser.add_argument("-t", "--type", action="store", default="A")
    parser.add_argument("-s", "--server", action="store", default="8.8.8.8",
                        help="IP address of a dns server")
    return parser


def main():
    parser = init_argparser()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args(sys.argv[1:])
    domain_name, qtype, ns_server = args.domain_name, args.type, args.server
    if domain_name[-1] != ".": domain_name += "."
    qtype = TYPE2INT[qtype]
    p, _ = resolver.ask_serverok(domain_name, qtype, ns_server)
    for answer in p.answers:
        print(answer.rdata)

if __name__ == "__main__":
    main()
