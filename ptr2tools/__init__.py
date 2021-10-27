from typing import BinaryIO
from .int import IntFile


def get_int_from_file(fp: BinaryIO) -> IntFile:
    """
    Gets an IntFile from a file stream.
    """
    return IntFile(fp)


def get_int_from_path(path: str) -> IntFile:
    """
    Gets an IntFile from a file path.
    """
    with open(path, "rb") as file:
        file.seek(0)
        return get_int_from_file(file)
