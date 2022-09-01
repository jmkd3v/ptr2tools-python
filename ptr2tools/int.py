from __future__ import annotations

import io
import sysconfig

from pathlib import Path
from dataclasses import dataclass
from enum import IntEnum
from typing import List, BinaryIO

# Logging
from logging import getLogger

# C garbage
import ctypes
from ctypes import cdll

logger = getLogger("ptr2tools")

EXT_SUFFIX = sysconfig.get_config_var("EXT_SUFFIX")
LIB_PATH = Path(__file__).parent.parent / f"lzss{EXT_SUFFIX}"
logger.debug(f"loading LZSS library from {LIB_PATH}")
lzss = cdll.LoadLibrary(str(LIB_PATH))


class IntChunkType(IntEnum):
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


@dataclass
class IntChunk:
    type: IntChunkType
    files: List[IntFile]

    @classmethod
    def load(cls, stream: BinaryIO) -> IntChunk:
        logger.debug("abc")

        # The offsets are relative to the start of the chunk, so I do a tell here to determine where that is
        chunk_offset = stream.tell()
        magic = stream.read(4)
        if magic != b"\x11\x22\x33\x44":
            logger.debug(f"magic is invalid, got {magic}")
            raise ValueError(f"magic is invalid")

        file_count = int.from_bytes(stream.read(4), byteorder="little")
        chunk_type = IntChunkType(int.from_bytes(stream.read(4), byteorder="little"))

        if chunk_type == IntChunkType.end:
            # we don't need to keep reading
            return cls(type=IntChunkType.end, files=[])

        files: List[IntFile] = []

        info_offset = int.from_bytes(stream.read(4), byteorder="little")
        data_offset = int.from_bytes(stream.read(4), byteorder="little")
        data_size = int.from_bytes(stream.read(4), byteorder="little")

        if stream.read(8) != b"\x00" * 8:
            raise ValueError("nul bytes missing")

        file_offsets = []
        for file_index in range(file_count + 1):  # i think there is an extra offset for some reason
            file_offsets.append(int.from_bytes(stream.read(4), byteorder="little"))

        stream.seek(chunk_offset + info_offset)

        # list of name offset and compressed file size
        file_name_offsets = []
        file_lengths = []
        for file_index in range(file_count):
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

        for file_index in range(file_count):
            file_name = file_names[file_index]
            file_offset = file_offsets[file_index]
            file_length = file_lengths[file_index]

            uncompressed_stream.seek(file_offset)

            files.append(IntFile(
                name=file_name,
                contents=uncompressed_stream.read(file_length)
            ))

        return cls(
            type=chunk_type,
            files=files
        )

    def dump(self, stream: BinaryIO):
        stream.write(b"\x11\x22\x33\x44")
        stream.write(len(self.files).to_bytes(4, "little"))
        stream.write(self.type.value.to_bytes(4, "little"))

        file_lengths = [len(file.contents) for file in self.files]
        file_offsets = [sum(file_lengths[:i]) for i in range(len(file_lengths) + 1)]
        file_offsets_blob = b"".join(file_offset.to_bytes(4, "little") for file_offset in file_offsets)

        data_blob = b"".join(file.contents for file in self.files)

        # compress
        misc_buffer = ctypes.create_string_buffer(0x2000)
        uncompressed_buffer = ctypes.create_string_buffer(data_blob)

        compressed_length = lzss.lzss_compress(
            12, 4, 2, 2,
            misc_buffer,
            uncompressed_buffer, len(data_blob),
            None
        )

        compressed_buffer = ctypes.create_string_buffer(compressed_length)

        lzss.lzss_compress(
            12, 4, 2, 2,
            misc_buffer,
            uncompressed_buffer, len(data_blob),
            compressed_buffer
        )

        compressed_data = compressed_buffer.raw

        # done!
        file_names = [file.name.encode("ascii") + b"\x00" for file in self.files]
        file_name_lengths = [len(name) for name in file_names]
        file_name_offsets = [sum(file_name_lengths[:i]) for i in range(len(file_lengths))]  # note - +1 is absent here.
        names_blob = b"".join(file_names)

        info_offset = 0x20 + len(file_offsets_blob)

        data_size = len(data_blob)

        info_blob = b"".join(
            file_name_offset.to_bytes(4, "little") + file_length.to_bytes(4, "little")
            for file_name_offset, file_length in zip(file_name_offsets, file_lengths)
        )

        data_offset = len(info_blob) + len(names_blob)

        stream.write(info_offset.to_bytes(4, "little"))
        stream.write(data_offset.to_bytes(4, "little"))
        stream.write((compressed_length + 8).to_bytes(4, "little"))
        stream.write(b"\x00"*8)

        stream.write(file_offsets_blob)
        stream.write(info_blob)
        stream.write(names_blob)

        stream.write(data_size.to_bytes(4, "little"))
        stream.write((compressed_length + 8).to_bytes(4, "little"))
        stream.write(compressed_data)


@dataclass
class IntContainer:
    chunks: List[IntChunk]

    @classmethod
    def load(cls, stream: BinaryIO) -> IntContainer:
        chunks = []

        while True:
            chunk = IntChunk.load(stream)

            if chunk.type == IntChunkType.end:
                break

            chunks.append(chunk)

        return cls(chunks)

    def dump(self, stream: BinaryIO):
        for chunk in self.chunks:
            chunk.dump(stream)
        IntChunk(type=IntChunkType.end, files=[]).dump(stream)  # dump the phantom chunk ghost!
