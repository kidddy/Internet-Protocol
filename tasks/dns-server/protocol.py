
import bitstring
import struct
import hexdump


ENCODING = "ascii"

def name2query(domain_name: str, domain_map=dict()) -> (bytes, dict):
    """Translates domain to bytes object.

    Args:
        domain_name: simple str domain, for example "duckduckgo.com"
        domain_map: dict: domain => int:position in package,
            it uses for compression.

    Return tuple:
        bytes - translated domain name
        dict - domain local map (need to update generic domain_map)
    """
    b_res = b""
    d_res = dict() 
    if domain_name == ".": return b_res + b"\x00", d_res
    pos = 0
    while domain_name != "":
        if domain_name in domain_map:
            b_res += struct.pack(">H", domain_map[domain_name] | 0b1100000000000000)
            return b_res, d_res
        d_res[domain_name] = pos
        part, _, domain_name = domain_name.partition(".")
        pos += len(part) + 1
        b_res += bytes([len(part)]) + part.encode(ENCODING)
    return b_res + b"\x00", d_res


class Question:

    body_format = ">HH"

    QTYPE_A = 1
    QTYPE_NS = 2

    QCLASS_IN = 1

    def __init__(self, domain_name: str, qtype: int, qclass=QCLASS_IN):
        self.domain_name = domain_name
        self.type = qtype
        self.cls = qclass

    def encode(self, domain_map=dict(), position=None) -> bytes:
        b_name, d_map = name2query(self.domain_name, domain_map)
        res = b_name + struct.pack(Question.body_format,
                                    self.type, self.cls)
        if position is None: return res
        domain_map.update({name: d_map[name] + position for name in d_map
                           if name not in domain_map})
        return res

    def pprint(self):
        indent = " " * 4
        yield "Question:"
        yield indent + "domain_name: {}".format(self.domain_name)
        yield indent + "type: {}".format(self.type)
        yield indent + "cls: {}".format(self.cls)

    def hexdump(self):
        yield from hexdump.dumpgen(self.encode())

    def copy(self, **kwargs):
        if ("domain_name" not in kwargs): kwargs["domain_name"] = self.domain_name
        if ("qtype" not in kwargs): kwargs["qtype"] = self.type
        if ("qclass" not in kwargs): kwargs["qclass"] = self.cls
        return Question(**kwargs)


class Answer(Question):

    body_format = ">HHIH"
    
    def __init__(self,domain_name: str, qtype: int, qclass: int,
                 ttl: int, rdata: str):
        super().__init__(domain_name, qtype, qclass)
        self.ttl = ttl
        self.rdata = rdata

    def encode(self, domain_map=dict(), position=None) -> bytes:
        res = super().encode(domain_map, position)
        position += len(res)

        b_rdata = b""
        if self.type == Answer.QTYPE_A:
            b_rdata = bytes(int(octet) for octet in self.rdata.split('.'))
        elif self.type == Answer.QTYPE_NS:
            b_rdata, d_map = name2query(self.rdata, domain_map)
            if position is not None:
                domain_map.update({name: d_map[name] + position + 6 for name in d_map})

        res += struct.pack(">IH", self.ttl, len(b_rdata))
        return res + b_rdata

    def pprint(self):
        indent = " " * 4
        yield "Answer:"
        yield indent + "domain_name: {}".format(self.domain_name)
        yield indent + "type: {}".format(self.type)
        yield indent + "cls: {}".format(self.cls)
        yield indent + "ttl: {}".format(self.ttl)
        yield indent + "rdata: {}".format(self.rdata)

    def hexdump(self):
        yield from hexdump.dumpgen(self.encode())

    def copy(self, **kwargs):
        if ("domain_name" not in kwargs): kwargs["domain_name"] = self.domain_name
        if ("qtype" not in kwargs): kwargs["qtype"] = self.type
        if ("qclass" not in kwargs): kwargs["qclass"] = self.cls
        if ("ttl" not in kwargs): kwargs["ttl"] = self.ttl
        if ("rdata" not in kwargs): kwargs["rdata"] = self.rdata
        return Answer(**kwargs)


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

    flags_format = "uint:1, uint:4, bool, bool, bool, bool, uint:3, uint:4"
    
    def __init__(self, QR, opcode, AA, TC, RD, RA, rcode):
        self.QR = QR
        self.opcode = opcode
        self.AA = AA
        self.TC = TC
        self.RD = RD
        self.RA = RA
        self.rcode = rcode

    def encode(self) -> bytes:
        return bitstring.pack(Flags.flags_format,
            self.QR,
            self.opcode,
            self.AA,
            self.TC,
            self.RD,
            self.RA,
            2,
            self.rcode).tobytes()

    def pprint(self):
        indent = " " * 4
        yield "flags:"
        yield indent + "QR: {}".format(self.QR)
        yield indent + "opcode: {}".format(self.opcode)
        yield indent + "AA: {}".format(self.AA)
        yield indent + "TC: {}".format(self.TC)
        yield indent + "RD: {}".format(self.RD)
        yield indent + "RA: {}".format(self.RA)
        yield indent + "rcode: {}".format(self.rcode)

    def hexdump(self):
        yield from hexdump.dumpgen(self.encode())

    def copy(self, **kwargs):
        if ("QR" not in kwargs): kwargs["QR"] = self.QR
        if ("opcode" not in kwargs): kwargs["opcode"] = self.opcode
        if ("AA" not in kwargs): kwargs["AA"] = self.AA
        if ("TC" not in kwargs): kwargs["TC"] = self.TC
        if ("RD" not in kwargs): kwargs["RD"] = self.RD
        if ("RA" not in kwargs): kwargs["RA"] = self.RA
        if ("rcode" not in kwargs): kwargs["rcode"] = self.rcode
        return Flags(**kwargs)


class Package:

    header_format = ">H2sHHHH"

    def __init__(self, identification: int, flags: Flags,
                 questions=[], answers=[], access_rights=[], extra_records=[]):
        self.identification = identification
        self.flags = flags
        self._questions = list(questions)
        self._answers = list(answers)
        self._access_rights = list(access_rights)
        self._extra_records = list(extra_records)

    @property
    def questions(self):
        return tuple(question for question in self._questions)
    
    @property
    def answers(self):
        return tuple(answer for answer in self._answers)
    
    @property
    def access_rights(self):
        return tuple(record for record in self._access_rights)
    
    @property
    def extra_records(self):
        return tuple(record for record in self._extra_records)
    
    def encode(self, compress=True) -> bytes:
        result = b""
        header = struct.pack(Package.header_format,
            self.identification,
            self.flags.encode(),
            len(self._questions),
            len(self._answers),
            len(self._access_rights),
            len(self._extra_records))
        result += header
        domain_map = dict()  # domain_name => position  TODO
        questions = ""  # .join((record.encode() for record in self._questions))
        for record in self._questions:
            result += record.encode(domain_map, len(result))
        for record in self._answers:
            result += record.encode(domain_map, len(result))
        for record in self._access_rights:
            result += record.encode(domain_map, len(result))
        for record in self._extra_records:
            result += record.encode(domain_map, len(result))
        return result

    def pprint(self):
        indent = " " * 4
        yield "DNS Package:"
        yield indent + "identification: {}".format(self.identification)
        yield from (indent + line for line in self.flags.pprint())
        for record in self._questions:
            yield from (indent + line for line in record.pprint())
        for record in self._answers:
            yield from (indent + line for line in record.pprint())
        for record in self._access_rights:
            yield from (indent + line for line in record.pprint())
        for record in self._extra_records:
            yield from (indent + line for line in record.pprint())

    def hexdump(self):
        yield from hexdump.dumpgen(self.encode())

    def copy(self, **kwargs):
        if ("identification" not in kwargs):
            kwargs["identification"] = self.identification
        if ("flags" not in kwargs): kwargs["flags"] = self.flags.copy()
        if ("questions" not in kwargs):
            records = []
            records.extend(record.copy() for record in self._questions)
            kwargs["questions"] = records
        if ("answers" not in kwargs):
            records = []
            records.extend(record.copy() for record in self._answers)
            kwargs["answers"] = records
        if ("access_rights" not in kwargs):
            records = []
            records.extend(record.copy() for record in self._access_rights)
            kwargs["access_rights"] = records
        if ("extra_records" not in kwargs):
            records = []
            records.extend(record.copy() for record in self._extra_records)
            kwargs["extra_records"] = records
        return Package(**kwargs)


class PackageParser:
    def __init__(self, pkg: bytes):
        self._pkg = pkg
        self._pos = 0

    def _data(self, length: int):
        return self._pkg[self._pos: self._pos + length]

    def _consume(self, length: int):
        self._pos += length

    def _read_name(self, start_idx) -> str:
        res = []
        idx = start_idx;
        while True:
            length = self._pkg[idx]
            if length >= 192:
                next_idx = struct.unpack(">H", self._pkg[idx: idx + 2])[0]
                next_idx -= struct.unpack(">H", b"\xc0\x00")[0]
                name, _ = self._read_name(next_idx)
                res.append(name)
                return ".".join(part for part in res), idx + 2 - start_idx
            if length==0:
                return ".".join(part for part in res) + ".", idx + 1 - start_idx
            res.append(self._pkg[idx+1: idx+1+length].decode(ENCODING))
            idx += 1 + length

    def parseQuestion(self) -> Question:
        name, to_consume = self._read_name(self._pos)
        self._consume(to_consume)
        unpacker = struct.Struct(Question.body_format)
        qtype, qclass = unpacker.unpack(self._data(unpacker.size))
        self._consume(unpacker.size)
        return Question(name, qtype, qclass)

    def parseAnswer(self) -> Answer:
        name, to_consume = self._read_name(self._pos)
        self._consume(to_consume)
        unpacker = struct.Struct(Answer.body_format)
        qtype, qclass, ttl, rdata_length = unpacker.unpack(self._data(unpacker.size))
        self._consume(unpacker.size)

        rdata = ""
        if (qtype == Answer.QTYPE_A):
            rdata = ".".join(str(octet) for octet in self._data(rdata_length))
        elif (qtype == Answer.QTYPE_NS):
            rdata, _ = self._read_name(self._pos)
        else:
            rdata = self._data(rdata_length)
        self._consume(rdata_length)
        return Answer(name, qtype, qclass, ttl, rdata)

    def parseFlags(self) -> Flags:
        data = self._data(2)
        self._consume(2)
        flgs = bitstring.BitArray(data).unpack(Flags.flags_format)
        QR, opcode, AA, TC, RD, RA, _, rcode = flgs
        return Flags(QR, opcode, AA, TC, RD, RA, rcode)

    def parsePackage(self) -> Package:
        identification = struct.unpack(">H", self._data(2))[0]
        self._consume(2)
        flgs = self.parseFlags()
        q, a, ar, er = struct.unpack(">HHHH", self._data(8))
        self._consume(8)
        questions = [self.parseQuestion() for _ in range(q)]
        answers = [self.parseAnswer() for _ in range(a)]
        access_rights = [self.parseAnswer() for _ in range(ar)]
        extra_records = [self.parseAnswer() for _ in range(er)]
        return Package(identification, flgs, questions, answers,
                       access_rights, extra_records)


class PackageBuilder:
    def __init__(self, identification: int):
        self.identification = identification
        self._flags = {"QR": Flags.QR_REQ,
                       "opcode": Flags.OPCODE_STD,
                       "AA": False,
                       "TC": False,
                       "RD": True,
                       "RA": False,
                       "rcode": Flags.RCODE_OK}
        self._questions = []
        self._answers = []

    def add_question(self, domain_name, qtype, qclass=Question.QCLASS_IN):
        self._questions.append(Question(domain_name, qtype, qclass))

    def add_answer(self, domain_name, qtype, ttl, rdata,
                   qclass=Answer.QCLASS_IN):
        self._answers.append(Answer(domain_name, qtype, qclass, ttl, rdata))

    def set_flags(self, **kwargs):
        self._flags.update(kwargs)

    @property
    def question(self):
        return list(self._questions)

    @property
    def answers(self):
        return list(self._answers)

    def build(self):
        fl = Flags(**self._flags)
        return Package(self.identification, fl, self._questions, self._answers)
