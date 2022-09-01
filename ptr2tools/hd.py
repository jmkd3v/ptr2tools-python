from __future__ import annotations

import io
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, List

from .vag import VagFile


class HdChunkType(Enum):
    version = "Vers"
    header = "Head"
    vag_info = "Vagi"
    sample = "Smpl"
    sample_set = "Sset"
    program = "Prog"


class HdChunk: ...


@dataclass
class HdVersionChunk(HdChunk):
    major_version: int
    minor_version: int

    @classmethod
    def load(cls, stream: BinaryIO):
        stream.seek(2, 1)
        return cls(
            major_version=int.from_bytes(stream.read(1), "little"),
            minor_version=int.from_bytes(stream.read(1), "little")
        )


@dataclass
class HdHeaderChunk(HdChunk):
    hd_file_size: int
    bd_file_size: int
    program_chunk_offset: int
    sample_set_chunk_offset: int
    sample_chunk_offset: int
    vag_info_chunk_offset: int

    @classmethod
    def load(cls, stream: BinaryIO):
        return cls(
            hd_file_size=int.from_bytes(stream.read(4), "little"),
            bd_file_size=int.from_bytes(stream.read(4), "little"),
            program_chunk_offset=int.from_bytes(stream.read(4), "little"),
            sample_set_chunk_offset=int.from_bytes(stream.read(4), "little"),
            sample_chunk_offset=int.from_bytes(stream.read(4), "little"),
            vag_info_chunk_offset=int.from_bytes(stream.read(4), "little")
        )


@dataclass
class HdVagInfoItem:
    vag_offset: int
    sample_rate: int
    loop: bool


@dataclass
class HdVagInfoChunk(HdChunk):
    items: List[HdVagInfoItem]

    @classmethod
    def load(cls, stream: BinaryIO):
        start_pos = stream.tell()
        info_count = int.from_bytes(stream.read(4), "little")  # OFF BY ONE BTW...
        info_offsets = []
        for info_index in range(info_count + 1):
            info_offsets.append(int.from_bytes(stream.read(4), "little"))

        items = []
        for info_offset in info_offsets:
            stream.seek((start_pos - 12) + info_offset)  # it's relative to chunk start! is 12 bytes in from start

            items.append(HdVagInfoItem(
                vag_offset=int.from_bytes(stream.read(4), "little"),
                sample_rate=int.from_bytes(stream.read(2), "little"),
                loop=stream.read(1) == b"\x01"
            ))

        return cls(
            items=items
        )


_CHUNK_TYPE_INDEX = {
    HdChunkType.version: HdVersionChunk,
    HdChunkType.header: HdHeaderChunk,
    HdChunkType.vag_info: HdVagInfoChunk,
    # HdChunkType.sample: HdSampleChunk,
    # HdChunkType.sample_set: HdSampleSetChunk
}


def _read_chunk(stream: BinaryIO, chunk_type: HdChunkType):
    raw_creator_name = stream.read(4)
    if len(raw_creator_name) != 4:
        raise EOFError("No more data! :(")

    creator_name = raw_creator_name.decode("ascii")[::-1]
    if HdChunkType(stream.read(4).decode("ascii")[::-1]) != chunk_type:
        raise ValueError("chunk type doesn't match :(")

    chunk_size = int.from_bytes(stream.read(4), "little")
    chunk_stream = io.BytesIO(stream.read(chunk_size - 12))
    return _CHUNK_TYPE_INDEX[chunk_type].load(chunk_stream)


@dataclass
class HdFile:
    version_chunk: HdVersionChunk
    vag_info_chunk: HdVagInfoChunk

    @classmethod
    def load(cls, stream: BinaryIO) -> HdFile:
        version_chunk = _read_chunk(stream, HdChunkType.version)
        header_chunk = _read_chunk(stream, HdChunkType.header)

        stream.seek(header_chunk.vag_info_chunk_offset)
        vag_info_chunk = _read_chunk(stream, HdChunkType.vag_info)

        # stream.seek(header_chunk.program_chunk_offset)
        # program_chunk = _read_chunk(stream, HdChunkType.program)

        return cls(
            version_chunk=version_chunk,
            vag_info_chunk=vag_info_chunk
        )

    def get_vags(self, bd_stream: BinaryIO) -> List[VagFile]:
        vag_items = self.vag_info_chunk.items
        vags = []
        for vag_index, vag_item in enumerate(vag_items):
            if vag_index == len(vag_items) - 1:
                read_amount = None
            else:
                read_amount = vag_items[vag_index + 1].vag_offset - vag_item.vag_offset

            bd_stream.seek(vag_item.vag_offset)
            vag_data = bd_stream.read(read_amount)
            vags.append(VagFile(
                data=vag_data,
                sample_rate=vag_item.sample_rate
            ))
        return vags
