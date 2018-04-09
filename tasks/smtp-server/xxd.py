#!/usr/bin/python3


from sys import argv
from os.path import getsize
import sys


class Dumper:
    """These objects will dumps input databytes in xxd format."""
    def __init__(self, num_shift=5):
        self._num_line = 0
        self._shift = num_shift

    @property
    def shift(self):
        return self._shift

    @shift.setter
    def shift(self, value, errors="ignore"):
        if not (errors == "ignore" or errors == "strict"):
            raise ValueError("bad argument: errors.")
        if value < -1 and errors == "strict":
            raise ValueError("bad argument: value.")
        self._shift = value

    @staticmethod
    def count_shift(buffer_size):
        return len(str(buffer_size // 16 + 1))

    @staticmethod
    def file_iterator(f, size):
        def result():
            for _ in range(size):
                yield f.read(1)[0]
        return result()

    def _xxd(self, byte_sequence):
        line = hex(self._num_line)[2:].rjust(self._shift, "0") + ":    "
        num = 0
        endian = ""
        for byte in byte_sequence:
            if 31 < byte < 127:
                endian += chr(byte)
            else:
                endian += '.'
            line += hex(byte)[2:].rjust(2, "0") + " "
            num += 1
            if num % 4 == 0:
                line += " "
            if num == 16:
                yield line + " " + endian
                self._num_line += 1
                line = hex(self._num_line)[2:].rjust(self._shift, "0") + ":    "
                num = 0
                endian = ""
        if num != 0:
            line = line.ljust(57 + self._shift)
            self._num_line += 1
            yield line + " " + endian

    def __call__(self, *args, **kwargs):
        try:
            yield from self._xxd(*args, **kwargs)
        except BrokenPipeError:
            sys.exit(0)


def main():
    file_name = argv[1]
    size = getsize(file_name)
    shift = Dumper.count_shift(size)
    with open(file_name, mode='rb') as f:
        i = Dumper.file_iterator(f, size)
        xxd = Dumper(shift)
        try:
            for line in xxd(i):
                print(line)
        except BrokenPipeError:
            pass


if __name__ == '__main__':
    main()
