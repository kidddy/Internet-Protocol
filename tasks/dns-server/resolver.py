
import socket
import protocol


GOOGLE_DNS = ("8.8.8.8", 53)


def send_and_get(pkg: bytes, ns_server=GOOGLE_DNS):
    """Send pkg to ns_server. Return answer package and respondent addr)"""
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.settimeout(5)
    sock.sendto(pkg, ns_server)
    answ, ns_server = sock.recvfrom(512)
    return answ, ns_server


def ask_server(name_question: str, qtype: int, ns_server):
    """Create package, send it to ns_server and return parsed answer"""
    pb = protocol.PackageBuilder(42)
    pb.set_flags(RA=True)
    pb.add_question(name_question, qtype, qclass=1)
    pkg = pb.build().encode()

    answ, _ = send_and_get(pkg)
    pp = protocol.PackageParser(answ)

    return pp.parsePackage()


def resolve_ns(name_question: str, qtype: int, ns_server):
    p = ask_server(name_question, qtype, ns_server)
    for answer in p.answers:
        d_name = answer.rdata
        print(d_name)
        p_answ = ask_server(d_name, protocol.Question.QTYPE_A, ns_server)
        for a in p_answ.answers:
            print("\t" + a.rdata)
