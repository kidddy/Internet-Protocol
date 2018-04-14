#!/usr/local/bin/python3


import protocol
import hexdump


def test_1():
    q = protocol.Question("yandex.ru", protocol.Question.QTYPE_A,
                          protocol.Question.QCLASS_IN)
    a = protocol.Answer("yandex.ru", protocol.Answer.QTYPE_A,
                        protocol.Answer.QCLASS_IN, 42, "127.0.0.1")
    fl = protocol.Flags(protocol.Flags.QR_REQ,
                        protocol.Flags.OPCODE_STD,
                        False, False, True, False,
                        protocol.Flags.RCODE_OK)
    p = protocol.Package(5, fl, [q], [a])
    data = p.encode()
    [print(line) for line in p.hexdump()]
    pp = protocol.PackageParser(data)
    pac = pp.parsePackage()
    [print(line) for line in p.hexdump()]
    [print(line) for line in pac.pprint()]


def test_2():
    header = b"\x00\x03\x01\x00\x00\x03\x00\x00\x00\x00\x00\x00"
    namef = b"\x06yandex"
    names = b"\x02ru"
    endn = b"\x00"
    type_a = b"\x00\x01"
    class_q = b"\x00\x01"
    name_sh = b"\xc0\x0c"
    data = header + namef + names + endn + type_a + class_q + name_sh + type_a + class_q + b"\x03www\xc0\x0c" + type_a + class_q
    [print(line) for line in hexdump.dumpgen(data)]
    pp = protocol.PackageParser(data)
    p = pp.parsePackage()
    [print(line) for line in p.pprint()]


def str_to_bytes(s):
    return bytes(int(byte, base=16) for byte in s.split(" "))


def test_3():
    data = str_to_bytes("db 42 01 00 00 01 00 01 00 00 00 00 03 77 77 77 "
                        "0c 6e 6f 72 74 68 65 61 73 74 65 72 6e 03 65 64 "
                        "75 00 00 01 00 01 c0 0c 00 01 00 01 00 00 02 58 "
                        "00 04 9b 21 11 44")
    pp = protocol.PackageParser(data)
    p = pp.parsePackage()
    [print(line) for line in p.hexdump()]


def main():
    test_3()


if __name__ == '__main__':
    main()
