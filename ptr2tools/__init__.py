from typing import BinaryIO
from .int import IntFile


def get_int_from_bytes(data: bytes) -> IntFile:
    """
    Gets an IntFile from the passed bytes.
    """
    return IntFile(data)


def get_int_from_file(fp: BinaryIO) -> IntFile:
    """
    Gets an IntFile from a file stream.
    """
    return IntFile(fp.read())


def get_int_from_path(path: str) -> IntFile:
    """
    Gets an IntFile from a file path.
    """
    with open(path, "rb") as file:
        return get_int_from_file(file)
