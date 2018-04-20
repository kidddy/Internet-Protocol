
import socket
import hexdump
import protocol

PORT = 53
GOOGLE_DNS = "8.8.8.8"

ROOT_SERVERS = {"a.root-servers.net.": "198.41.0.4",
                "b.root-servers.net.": "199.9.14.201",
                "c.root-servers.net.": "192.33.4.12",
                "d.root-servers.net.": "199.7.91.13",
                "e.root-servers.net.": "192.203.230.10",
                "f.root-servers.net.": "192.5.5.241",
                "g.root-servers.net.": "192.112.36.4",
                "h.root-servers.net.": "198.97.190.53",
                "i.root-servers.net.": "192.36.148.17",
                "j.root-servers.net.": "192.58.128.30",
                "k.root-servers.net.": "193.0.14.129",
                "l.root-servers.net.": "199.7.83.42",
                "m.root-servers.net.": "202.12.27.33"}

def send_and_get(pkg: bytes, ns_server=GOOGLE_DNS):
    """Send pkg to ns_server. Return answer package and respondent addr)"""
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.settimeout(5)
    sock.sendto(pkg, (ns_server, PORT))
    answ, ns_server = sock.recvfrom(512)
    return answ, ns_server


def ask_server(name_question: str, qtype: int, ns_server):
    """Create package, send it to ns_server and return parsed answer"""
    pb = protocol.PackageBuilder(42)
    pb.set_flags(RA=True)
    pb.add_question(name_question, qtype, qclass=1)
    pkg = pb.build().encode()
    [print(line) for line in hexdump.dumpgen(pkg)]

    answ, _ = send_and_get(pkg, ns_server)
    pp = protocol.PackageParser(answ)

    return pp.parsePackage(), answ


def resolve_ns(name_question: str, qtype: int, ns_server):
    p = ask_server(name_question, qtype, ns_server)
    for answer in p.answers:
        d_name = answer.rdata
        print(d_name)
        p_answ = ask_server(d_name, protocol.Question.QTYPE_A, ns_server)
        for a in p_answ.answers:
            print("\t" + a.rdata)
