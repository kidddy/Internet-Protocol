#!/usr/local/bin/python3

import protocol
import hexdump
import cache
import time
import resolver


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
    data = header + namef + names + endn + type_a + class_q + name_sh + b"\x00\x02" + class_q + b"\x03www\xc0\x0c" + type_a + class_q
    [print(line) for line in hexdump.dumpgen(data)]
    pp = protocol.PackageParser(data)
    p = pp.parsePackage()
    [print(line) for line in p.pprint()]
    return p


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


def test_4():
    # Let's imagine that we are dns server and got std query
    query = test_2()
    # our cache:
    cache_A = {"yandex.ru": ("77.88.55.77", 1523853480, 30*60),
               "www.yandex.ru": ("5.255.255.70", 1523853480, 30*60)}
    cache_NS = {"yandex.ru": ("ns1.yandex.ru", 1523853480, 30*60)}
    cache = {protocol.Question.QTYPE_A: cache_A,
             protocol.Question.QTYPE_NS: cache_NS}
    #  Create answer package
    answers = []
    for question in query.questions:
        rdata, added, ttl = cache[question.type][question.domain_name]
        answers.append(protocol.Answer(
            question.domain_name,
            question.type,
            question.cls,
            int(ttl - (time.time() - added)),
            rdata))
    res = query.copy(flags=protocol.Flags(1, 1, False, False, True, True, 0),
                     answers=answers)
    [print(line) for line in res.hexdump()]
    [print(line) for line in res.pprint()]

def test_5():
    q = cache.Queue()
    e1 = q.add(10)
    e2 = q.add(11)
    e3 = q.add(12)
    q.remove(e3)
    print(q.pop())
    print(q.pop())


def test_6():
    q = protocol.Question("h.root-servers.net.", protocol.Question.QTYPE_A)
    fl = protocol.Flags(protocol.Flags.QR_REQ,
                        protocol.Flags.OPCODE_STD,
                        False, False, True, False,
                        protocol.Flags.RCODE_OK)
    p = protocol.Package(5, fl, [q])
    data = p.encode()
    answ, _ = resolver.send_and_get(data)
    pp = protocol.PackageParser(answ)
    p = pp.parsePackage()
    [print(line) for line in p.pprint()]

def test_7():
    p, data = resolver.ask_server("ru.", protocol.Question.QTYPE_NS,
                                  "198.41.0.4")
    [print(line) for line in p.pprint()]
    [print(line) for line in hexdump.dumpgen(data)]

def main():
    test_7()


if __name__ == '__main__':
    main()
