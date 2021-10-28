from typing import BinaryIO
from .int import IntContainer


def get_int_from_bytes(data: bytes) -> IntContainer:
    """
    Gets an IntFile from the passed bytes.
    """
    return IntContainer(data)


def get_int_from_file(fp: BinaryIO) -> IntContainer:
    """
    Gets an IntFile from a file stream.
    """
    return IntContainer(fp.read())


def get_int_from_path(path: str) -> IntContainer:
    """
    Gets an IntFile from a file path.
    """
    with open(path, "rb") as file:
        file.seek(0)
        return get_int_from_file(file)
