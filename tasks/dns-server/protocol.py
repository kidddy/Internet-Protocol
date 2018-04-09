#!/usr/bin/python3


import bitstring
import struct


ENCODING = "ascii"

def name2query(domain_name: str) -> bytes:
    res = bytes()
    for part in domain_name.split("."):
        res += bytes([len(part)]) + part.encode(ENCODING)
    res += bytes([0])
    return res


def query2name(query: bytes) -> (str, bytes):
    res = []
    idx = 0;
    while True:
        length = query[idx]
        if length==0:
            return (".".join(part for part in res), query[idx+1:])
        res.append(query[idx+1: idx+1+length].decode(ENCODING))
        idx += 1 + length


class Question:

    body_format = ">HH"

    QTYPE_A = 1
    QTYPE_NS = 2

    QCLASS_IN = 1

    def __init__(self, domain_name: str, q_type: int, q_class=QCLASS_IN):
        self.domain_name = domain_name
        self.type = q_type
        self.cls = q_class

    def encode(self) -> bytes:
        b_name = name2query(self.domain_name)
        return b_name + struct.pack(Question.__body_format,
                                    self.type, self.cls)


class Flags:
    """QR - query type:
        0 - request
        1 - answer
    opcode - operation code:
        0 - std query, 1 - inverse query, 2 - server status request
    AA - authoritative answer
    TC - truncated
    RD - recursion desired
    RA - recursion available
    rcode - return code:
        0 - ok
        1 - format error
        2 - server failure
        3 - name error
        4 - not implemented
        5 - refused
    """

    QR_REQ = 0
    QR_ANS = 1

    OPCODE_STD = 0
    OPCODE_INV = 1
    OPCODE_SSR = 2

    RCODE_OK = 0
    RCODE_FMT = 1
    RCODE_SF = 2
    RCODE_NM = 3
    RCODE_NI = 4
    RCODE_RD = 5

    flasgs_format = "uint:1, uint:4, bool, bool, bool, bool, uint:3, uint:4"
    
    def __init__(self, QR, opcode, AA, TC, RD, RA, rcode):
        self.QR = QR
        self.opcode = opcode
        self.AA = AA
        self.TC = TC
        self.RD = RD
        self.RA = RA
        self.rcode = rcode

    def encode(self) -> bytes:
        return bitstring.pack(Flags.__format,
            self.QR,
            self.opcode,
            self.AA,
            self.TC,
            self.RD,
            self.RA,
            0,
            self.rcode).tobytes()

    #  @classmethod
    #  def decode(cls, data: bytes):
        #  QR, opcode, AA, TC, RD, RA, _, rcode = bitstring.BitArray(data).unpack(
            #  Flags.__format)
        #  return cls(QR, opcode, AA, TC, RD, RA, rcode)


class Package:

    header_format = ">H2sHHHH"

    def __init__(self, identification: int, flags: Flags,
                 questions, answers, access_rights, extra_records):
        self.identification = identification
        self.flags = flags
        self._questions = list(questions)
        self._answers = list(answers)
        self._access_rights = list(access_rights)
        self._extra_records = list(extra_records)

    @property
    def questions(self):
        return (question for question in self._questions)
    
    @property
    def answers(self):
        return (answer for answer in self._answer)
    
    @property
    def access_rights(self):
        return (record for record in self._access_rights)
    
    @property
    def extra_records(self):
        return (record for record in self._extra_records)
    
    def encode(self) -> bytes:
        header = struct.pack(Package.__header_format,
            self.identification,
            self.flags.encode(),
            len(self._questions),
            len(self._answers),
            len(self._access_rights),
            len(self._extra_records))
        questions = b"".join((record.encode() for record in self._questions))
        answers = b"".join((record.encode() for record in self._answers))
        access_rights = b"".join((record.encode() for record in self._access_rights))
        extra_records = b"".join((record.encode() for record in self._extra_records))
        return header + questions + answers + access_rights + extra_records


class PackageParser:
    def __init__(self, pkg: bytes):
        self._pkg = pkg

    def _data(self, length: int):
        return self._pkg[:length)

    def _consume(self, length: int):
        self._pkg = self._pkg[length:]

    def _read_name(self) -> str:
        res = []
        idx = 0;
        while True:
            length = query[idx]
            if length==0:
                self._consume(idx+1)
                return ".".join(part for part in res)
            res.append(query[idx+1: idx+1+length].decode(ENCODING))
            idx += 1 + length

    def parseQuestion(self) -> Question:
        name = self._read_name()
        unpacker = struct.Struct(Question.body_format)
        qtype, qclass = unpacker.unpack(self._data(unpacker.size))
        self._consume(unpacker.size)
        raise Question(name, qtype, qclass)

    def parseFlags(self) -> Flags:
        data = self._data(2)
        self._consume(2)
        flgs = bitstring.BitArray(data).unpack(Flags.flasgs_format)
        QR, opcode, AA, TC, RD, RA, _, rcode = flgs
        return cls(QR, opcode, AA, TC, RD, RA, rcode)

    def parsePackage(self) -> Package:
        identification = struct.unpack(">H", self._data(2))
        self._consume(2)
        flgs = self.parseFlags()
        q, a, ar, er = struct.unpack(">HHHH", self._data(8))
        self._consume(8)
        questions = (self.parseQuestion() for _ in range(q))
        answers = (self.parseQuestion() for _ in range(a))
        access_rights = (self.parseQuestion() for _ in range(ar))
        extra_records = (self.parseQuestion() for _ in range(er))
        return Package(identification, flgs, questions, answers,
                       access_rights, extra_records)  # TODO Test me
