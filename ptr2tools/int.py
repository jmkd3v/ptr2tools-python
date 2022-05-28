import io
from pathlib import Path
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Dict, Optional, BinaryIO

import ctypes
from ctypes import cdll
lzss = cdll.LoadLibrary(str(Path(__file__).parent / "lzss.so"))


class ChunkType(IntEnum):
    end = 0
    textures = 1
    sounds = 2
    stage = 3
    red_hat = 4
    blue_hat = 5
    pink_hat = 6
    yellow_hat = 7


@dataclass
class IntFile:
    name: str
    contents: bytes


class IntChunk:
    def __init__(self, stream: BinaryIO):
        # The offsets are relative to the start of the chunk, so I do a tell here to determine where that is
        chunk_offset = stream.tell()

        if stream.read(4) != b"\x11\x22\x33\x44":
            raise ValueError("magic is not present")

        self.file_count = int.from_bytes(stream.read(4), byteorder="little")
        self.type = ChunkType(int.from_bytes(stream.read(4), byteorder="little"))
        self.files: List[IntFile] = []

        if self.type == ChunkType.end:
            return

        info_offset = int.from_bytes(stream.read(4), byteorder="little")
        data_offset = int.from_bytes(stream.read(4), byteorder="little")
        data_size = int.from_bytes(stream.read(4), byteorder="little")

        if stream.read(8) != b"\x00" * 8:
            raise ValueError("nul bytes missing")

        file_offsets = []
        for file_index in range(self.file_count):  # i think there is an extra offset for some reason
            file_offsets.append(int.from_bytes(stream.read(4), byteorder="little"))

        stream.seek(chunk_offset + info_offset)  # not exactly sure why the +4 here but whatever?

        # list of name offset and compressed file size
        file_name_offsets = []
        file_lengths = []
        for file_index in range(self.file_count):
            file_name_offsets.append(int.from_bytes(stream.read(4), byteorder="little"))
            file_lengths.append(int.from_bytes(stream.read(4), byteorder="little"))

        # now we compile this all together

        # reading null-terminated strings in python is a PITA and can be slow
        # i cheat around it by just reading everything until the file contents start and then just splitting by NUL
        name_data = stream.read((
                (chunk_offset + data_offset + info_offset) - stream.tell()  # data offset is relative to info offset
        )).strip(b"\x00").decode("ascii")
        file_names = name_data.split("\x00")

        # now we are right at the start of the data, so we can just read data_size bytes
        uncompressed_size = int.from_bytes(stream.read(4), byteorder="little")
        compressed_size = int.from_bytes(stream.read(4), byteorder="little")

        misc_buffer = ctypes.create_string_buffer(0x1000)

        compressed_buffer = ctypes.create_string_buffer(stream.read(data_size - 8))
        uncompressed_buffer = ctypes.create_string_buffer(uncompressed_size)

        lzss.lzss_decompress(
            12, 4, 2, 2,
            misc_buffer,
            compressed_buffer,
            compressed_size,
            uncompressed_buffer,
            uncompressed_size,
        )

        uncompressed_stream = io.BytesIO(uncompressed_buffer.raw)

        for file_index in range(self.file_count):
            file_name = file_names[file_index]
            file_offset = file_offsets[file_index]
            file_length = file_lengths[file_index]

            uncompressed_stream.seek(file_offset)

            self.files.append(IntFile(
                name=file_name,
                contents=uncompressed_stream.read(file_length)
            ))


class IntContainer:
    def __init__(self, stream: BinaryIO):
        self.chunks = []

        while True:
            chunk = IntChunk(stream)

            if chunk.type == ChunkType.end:
                break

            self.chunks.append(chunk)
