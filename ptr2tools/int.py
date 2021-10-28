from typing import List, Tuple
from enum import IntEnum

chunk_splitter = int.to_bytes(0x44332211, 4, "little")
offsets_size = 4
name_offsets_size = 8


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

        true_info_offset = self.header.info_offset - 4  # the true offset is 4 less than this.
        true_contents_offset = true_info_offset + self.header.contents_offset  # the contents offset is relative to info
        true_info_data = data[true_info_offset:true_contents_offset]

        # because the data is relative to the file count we can just multiply by 8 to get the proper spot
        # I have to subtract by 4 for some reason
        split_position: int = (self.header.file_count * 8)

        file_name_size_data = true_info_data[:split_position]

        file_name_data = true_info_data[split_position:]
        file_offset_data = data[28:true_info_offset]

        for i in range(0, len(file_name_size_data), 8):
            name_offset = int.from_bytes(bytes=file_name_size_data[i:i+4], byteorder="little")
            file_name: str = file_name_data[name_offset:].split(b"\x00")[0].decode("utf-8")
            file_size: int = int.from_bytes(bytes=file_name_size_data[i+4:i+8], byteorder="little")


class IntFile:
    """
    Represents an .INT file in a PaRappa The Rapper 2 ISO.
    """

    def __init__(self, data: bytes):
        self.data: bytes = data
        # we split the first item in the split.
        self.chunks: List[IntFileChunk] = [IntFileChunk(
            data=chunk_data
        ) for chunk_data in self.data.split(chunk_splitter)[1:-1]]  # remove first and last item.
