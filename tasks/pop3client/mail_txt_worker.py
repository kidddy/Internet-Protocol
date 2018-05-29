#!/usr/bin/python3

import re
import sys

from base64 import b64decode
from pprint import pprint
from email.header import decode_header


RE_SEP_HEADER = re.compile(r"(.*?)\n\n(.*)", re.MULTILINE | re.DOTALL)


def get_head_and_body(msg: str) -> (str, str):
    m = RE_SEP_HEADER.search(msg)
    head, body = "", ""
    if m:
        head = m.group(1)
        body = m.group(2)
    return head, body


def parse_head(head: str):
    result = dict()
    last_key = ""
    for line in head.split("\n"):
        if line.startswith("\t") or line.startswith(" "):
            result[last_key] = "%s\n%s" % (result[last_key], line.strip())
        else:
            key, sep, value = line.partition(": ")
            result[key] = value.strip()
            last_key = key
    for key in result:
        m = RE_UTF_BLOCK.search(result[key])
        result[key] = decode_utf(result[key]) if m else result[key]
    return result


RE_UTF_BLOCK = re.compile(r"=\?.*?\?=")

def decode_utf(line: str) -> str:
    parse_res = decode_header(line)
    res = []
    for s, enc in parse_res:
        enc = enc if enc else "ascii"
        s = s if isinstance(s, bytes) else s.encode(enc)
        res.append(s.decode(enc))
    return " ".join(res)


def text_content_handler(body: str, head, subtype, properties):
    if subtype == "plain":
        transfer_enc = head["Content-Transfer-Encoding"] \
            if "Content-Transfer-Encoding" in head else "NONE"
        if transfer_enc == "base64":
            charset = properties["charset"][1:-1]
            body = b64decode(body).decode(charset)
        elif transfer_enc == "NONE":
            pass
        else:
            return "Error: unknown Content-Transfer-Encoding"
        return body.strip()
    return "Error: Not implemented text subtype"


def image_content_handler(body: str, head, subtype, properties):
    transfer_enc = head["Content-Transfer-Encoding"] \
        if "Content-Transfer-Encoding" in head else "NONE"
    if transfer_enc == "base64":
        filename = properties["name"][1:-1]
        pic = b64decode(body)
        with open(filename, mode='wb') as f:
            f.write(pic)
        return f"""\n- - - - - - - - - - - -
Pictute saved: {filename}
 - - - - - - - - - - - - """
    else:
        return f"Error: unknown Content-Transfer-Encoding - {transfer_enc}"

    return "Error: soon ..."


def multipart_content_handler(body: str, head, subtype, properties):
    bound = properties["boundary"][1: -1]  # remove quotes
    start_bound = f"--{bound}\n"
    end_bound1 = f"\n{bound}--"
    end_bound2 = f"\n--{bound}--"
    body = body.split(end_bound1)[0]
    body = body.split(end_bound2)[0]
    parts = body.split(start_bound)
    parts.pop(0)
    if subtype == "alternative":
        for alternative in parts:
            head, body = parse_mail(alternative)
            if not body.startswith("Error"): return body
        return "Error: no alternative supported"
    elif subtype == "mixed":
        res_parts = []
        for part in parts:
            head, body = parse_mail(part)
            res_parts.append(body)
        return "\n".join(res_parts)
    return "Error: Not supported content subtype"


CONTENT_HANDLER = dict()
CONTENT_HANDLER["text"] = text_content_handler
CONTENT_HANDLER["multipart"] = multipart_content_handler
CONTENT_HANDLER["image"] = image_content_handler


RE_CONTENT_TYPE = re.compile(r"(\w+)/(\w+);(?:\s(.*))?")
DEFAULT_CONTENT_TYPE = "text/plain; charset=UTF-8"

def parse_body(body: str, head: dict) -> str:
    content_type = head["Content-Type"] if "Content-Type" in head \
        else DEFAULT_CONTENT_TYPE
    m = RE_CONTENT_TYPE.search(content_type)
    content_type = m.group(1)
    content_subtype = m.group(2)
    properties_str = m.group(3)
    content_properties = dict()
    if properties_str:
        for content_property in properties_str.split("; "):
            key, sep, value = content_property.partition("=")
            content_properties[key] = value
    # content_properties = dict(content_property.split("=") \
        # for content_property in properties.split("; ")) if m.group(3) \
        # else dict()
    if content_type not in CONTENT_HANDLER:
        return f"Error: not supported content-type - {content_type}"
    return CONTENT_HANDLER[content_type](body, head, content_subtype,
                                         content_properties)


def parse_mail(letter: str) -> (str, str):
    head, body = get_head_and_body(letter)
    head = parse_head(head)
    body = parse_body(body, head)
    return (head, body)


def main():
    with open(sys.argv[1]) as f:
        t = f.read()
    head, body = parse_mail(t)
    print(body)


if __name__ == "__main__":
    main()
