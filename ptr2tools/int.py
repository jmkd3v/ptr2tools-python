from enum import IntEnum
from typing import List
from dataclasses import dataclass

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


class IntHeader:
    """
    Represents the .INT file's header.
    """

    def __init__(self, data: bytes):
        self.file_count: int = int.from_bytes(bytes=data[:4], byteorder="little")
        self.resource_type: IntResourceType = IntResourceType(int.from_bytes(bytes=data[4:8], byteorder="little"))
        self.info_offset: int = int.from_bytes(bytes=data[8:12], byteorder="little")
        self.contents_offset: int = int.from_bytes(bytes=data[12:16], byteorder="little")
        self.compressed_size: int = int.from_bytes(bytes=data[16:20], byteorder="little")


@dataclass()
class IntFile:
    """
    Represents a file inside of an .INT file.
    """
    number: int
    name: str
    size: int
    compressed_contents: bytes


class IntChunk:
    """
    Represents a single chunk in an .INT file.
    """

    def __init__(self, data: bytes):
        self.header: IntHeader = IntHeader(data[:20])
        self.files: List[IntFile] = []

        true_info_offset = self.header.info_offset - 4  # the true offset is 4 less than this.
        true_contents_offset = true_info_offset + self.header.contents_offset  # the contents offset is relative to info
        true_info_data = data[true_info_offset:true_contents_offset]

        # because the data is relative to the file count we can just multiply by 8 to get the proper spot
        # I have to subtract by 4 for some reason
        split_position: int = (self.header.file_count * 8)

        file_name_size_data = true_info_data[:split_position]

        file_name_data = true_info_data[split_position:]
        file_offset_data = data[28:true_info_offset]
        file_contents_data = data[true_contents_offset:]

        for file_number in range(0, self.header.file_count):
            f_offset = file_number * 4
            fn_offset = file_number * 8  # offset for the file name offset + size data

            content_offset = int.from_bytes(bytes=file_offset_data[f_offset:f_offset+4], byteorder="little")
            name_offset = int.from_bytes(bytes=file_name_size_data[fn_offset:fn_offset+4], byteorder="little")
            file_name: str = file_name_data[name_offset:].split(b"\x00")[0].decode("utf-8")
            file_size: int = int.from_bytes(bytes=file_name_size_data[fn_offset+4:fn_offset+8], byteorder="little")
            compressed_contents: bytes = file_contents_data[content_offset:file_size]

            self.files.append(IntFile(
                number=file_number,
                name=file_name,
                size=file_size,
                compressed_contents=compressed_contents
            ))


class IntContainer:
    """
    Represents an .INT file in a PaRappa The Rapper 2 ISO.
    """

    def __init__(self, data: bytes):
        self.data: bytes = data
        # we split the first item in the split.
        self.chunks: List[IntChunk] = [IntChunk(
            data=chunk_data
        ) for chunk_data in self.data.split(chunk_splitter)[1:-1]]  # remove first and last item.
