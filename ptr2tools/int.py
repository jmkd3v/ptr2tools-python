from typing import List
from enum import IntEnum

chunk_splitter = int.to_bytes(0x44332211, 4, "little")


class IntResourceType(IntEnum):
    end = 0
    tm0 = 1
    sounds = 2
    stage = 3
    red_hat = 4
    blue_hat = 5
    pink_hat = 6
    yellow_hat = 7


class IntFileHeader:
    """
    Represents the .INT file's header.
    """
    def __init__(self, data: bytes):
        self.file_count: int = int.from_bytes(bytes=data[:4], byteorder="little")
        self.resource_type: IntResourceType = IntResourceType(int.from_bytes(bytes=data[4:8], byteorder="little"))
        self.info_offset: int = int.from_bytes(bytes=data[8:12], byteorder="little")
        self.contents_offset: int = int.from_bytes(bytes=data[12:16], byteorder="little")
        self.compressed_size: int = int.from_bytes(bytes=data[16:20], byteorder="little")


class IntFileChunk:
    """
    Represents a single chunk in an .INT file.
    """
    def __init__(self, data: bytes):
        self.header: IntFileHeader = IntFileHeader(data[:20])
        self.info_data: bytes = data[self.header.info_offset:self.header.info_offset+self.header.contents_offset]
        self.contents_data: bytes = data[self.header.info_offset+self.header.contents_offset:]


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
