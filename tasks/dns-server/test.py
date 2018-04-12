#!/usr/local/bin/python3


import protocol
import hexdump


def main():
    q = protocol.Question("yandex.ru", protocol.Question.QTYPE_A,
                          protocol.Question.QCLASS_IN)
    fl = protocol.Flags(protocol.Flags.QR_REQ,
                        protocol.Flags.OPCODE_STD,
                        False, False, True, False,
                        protocol.Flags.RCODE_OK)
    p = protocol.Package(5, fl, [q])
    data = p.encode()
    [print(line) for line in hexdump.dumpgen(data)]
    pp = protocol.PackageParser(data)
    pac = pp.parsePackage()
    [print(line) for line in hexdump.dumpgen(pac.encode())]


if __name__ == '__main__':
    main()
