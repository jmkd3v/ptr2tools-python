from typing import List
from enum import IntEnum

chunk_splitter = int.to_bytes(0x44332211, 4, "little")


class IntResourceType(IntEnum):
    end = 0
    tm0 = 1
    sounds = 2
    stage = 3
    hat_color_base = 4

    # stupid hack because I do not know what 5-7 types are
    unknown_5 = 5
    unknown_6 = 6
    unknown_7 = 7


class IntFileHeader:
    """
    Represents the .INT file's header.
    """
    def __init__(self, data: bytes):
        self.file_count: int = int.from_bytes(bytes=data[:4], byteorder="little")
        try:
            self.resource_type: IntResourceType = IntResourceType(int.from_bytes(bytes=data[4:8], byteorder="little"))
        except Exception as exception:
            print(data)
            raise exception
        self.fn_table_offset: int = int.from_bytes(bytes=data[8:12], byteorder="little")
        self.fn_table_size: int = int.from_bytes(bytes=data[12:16], byteorder="little")
        self.lzss_section_size: int = int.from_bytes(bytes=data[16:20], byteorder="little")
        self.unk: List[int] = [
            int.from_bytes(bytes=data[20:24], byteorder="little"),
            int.from_bytes(bytes=data[24:28], byteorder="little"),
        ]


class IntFileChunk:
    """
    Represents a single chunk in an .INT file.
    """
    def __init__(self, data: bytes):
        self.header: IntFileHeader = IntFileHeader(data[:28])


class IntFile:
    """
    Represents an .INT file in a PaRappa The Rapper 2 ISO.
    """
    def __init__(self, data: bytes):
        self.data: bytes = data
        # we split the first item in the split.
        self.chunks: List[IntFileChunk] = [IntFileChunk(
            data=chunk_data
        ) for chunk_data in self.data.split(chunk_splitter)[1:]]
