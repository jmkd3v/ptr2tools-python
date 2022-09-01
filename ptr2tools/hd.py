from __future__ import annotations

import io
import math
from enum import Enum
from dataclasses import dataclass
from typing import BinaryIO, List, Optional

from .vag import VagFile


class HdChunkType(Enum):
    version = "Vers"
    header = "Head"
    vag_info = "Vagi"
    sample = "Smpl"
    sample_set = "Sset"
    program = "Prog"


class HdChunk:
    ...


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

    def dump(self, stream: BinaryIO):
        stream.write(b"\x00" * 2)
        stream.write(int.to_bytes(self.major_version, 1, "little"))
        stream.write(int.to_bytes(self.minor_version, 1, "little"))


@dataclass
class HdHeaderChunk(HdChunk):
    hd_size: int
    bd_size: int
    program_chunk_offset: int
    sample_set_chunk_offset: int
    sample_chunk_offset: int
    vag_info_chunk_offset: int

    @classmethod
    def load(cls, stream: BinaryIO):
        return cls(
            hd_size=int.from_bytes(stream.read(4), "little"),
            bd_size=int.from_bytes(stream.read(4), "little"),
            program_chunk_offset=int.from_bytes(stream.read(4), "little"),
            sample_set_chunk_offset=int.from_bytes(stream.read(4), "little"),
            sample_chunk_offset=int.from_bytes(stream.read(4), "little"),
            vag_info_chunk_offset=int.from_bytes(stream.read(4), "little")
        )

    def dump(self, stream: BinaryIO):
        stream.write(int.to_bytes(self.hd_size, 4, "little"))
        stream.write(int.to_bytes(self.bd_size, 4, "little"))
        stream.write(int.to_bytes(self.program_chunk_offset, 4, "little"))
        stream.write(int.to_bytes(self.sample_set_chunk_offset, 4, "little"))
        stream.write(int.to_bytes(self.sample_chunk_offset, 4, "little"))
        stream.write(int.to_bytes(self.vag_info_chunk_offset, 4, "little"))


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

    def dump(self, stream: BinaryIO):
        stream.write(int.to_bytes(len(self.items) - 1, 4, "little"))
        item_position = 16 + (len(self.items) * 4)

        for info_index in range(len(self.items)):
            stream.write(int.to_bytes(item_position + (8 * info_index), 4, "little"))

        for item in self.items:
            stream.write(int.to_bytes(item.vag_offset, 4, "little"))
            stream.write(int.to_bytes(item.sample_rate, 2, "little"))
            stream.write(b"\x01" if item.loop else b"\x00")
            stream.write(b"\xFF")


@dataclass
class HdSampleChunk:
    data: bytes

    @classmethod
    def load(cls, stream: BinaryIO):
        return cls(data=stream.read())

    def dump(self, stream: BinaryIO):
        stream.write(self.data)


@dataclass
class HdSampleSetChunk:
    data: bytes

    @classmethod
    def load(cls, stream: BinaryIO):
        return cls(data=stream.read())

    def dump(self, stream: BinaryIO):
        stream.write(self.data)


@dataclass
class HdProgramChunk:
    data: bytes

    @classmethod
    def load(cls, stream: BinaryIO):
        return cls(data=stream.read())

    def dump(self, stream: BinaryIO):
        stream.write(self.data)


_CHUNK_TYPE_CLASS = {
    HdChunkType.version: HdVersionChunk,
    HdChunkType.header: HdHeaderChunk,
    HdChunkType.vag_info: HdVagInfoChunk,
    HdChunkType.sample: HdSampleChunk,
    HdChunkType.sample_set: HdSampleSetChunk,
    HdChunkType.program: HdProgramChunk
}
_CHUNK_CLASS_TYPE = {v: k for k, v in _CHUNK_TYPE_CLASS.items()}


def _read_chunk(stream: BinaryIO, chunk_type: HdChunkType):
    raw_creator_name = stream.read(4)
    if len(raw_creator_name) != 4:
        raise EOFError("not enough data")

    if raw_creator_name.decode("ascii")[::-1] != "SCEI":
        raise ValueError("bad creator name")

    if HdChunkType(stream.read(4).decode("ascii")[::-1]) != chunk_type:
        raise ValueError("chunk type doesn't match :(")

    chunk_size = int.from_bytes(stream.read(4), "little")
    chunk_stream = io.BytesIO(stream.read(chunk_size - 12))
    return _CHUNK_TYPE_CLASS[chunk_type].load(chunk_stream)


def _write_chunk(stream: BinaryIO, chunk, length: Optional[int] = None):
    chunk_type: HdChunkType = _CHUNK_CLASS_TYPE[type(chunk)]
    stream.write(b"SCEI"[::-1])
    stream.write(chunk_type.value[::-1].encode("ascii"))

    chunk_stream = io.BytesIO()
    chunk.dump(chunk_stream)
    chunk_stream.seek(0)
    chunk_data = chunk_stream.read()
    del chunk_stream

    if length is None:
        length = 16 * math.ceil((len(chunk_data) + 12) / 16)
    pad_amount = (length - 12) - len(chunk_data)

    stream.write(int.to_bytes(length, 4, "little"))
    stream.write(chunk_data)
    stream.write(b"\xFF" * pad_amount)


@dataclass
class HdFile:
    bd_size: int
    version_chunk: HdVersionChunk
    vag_info_chunk: HdVagInfoChunk
    sample_chunk: HdSampleChunk
    sample_set_chunk: HdSampleSetChunk
    program_chunk: HdProgramChunk

    @classmethod
    def load(cls, stream: BinaryIO) -> HdFile:
        version_chunk = _read_chunk(stream, HdChunkType.version)
        header_chunk = _read_chunk(stream, HdChunkType.header)

        stream.seek(header_chunk.vag_info_chunk_offset)
        vag_info_chunk = _read_chunk(stream, HdChunkType.vag_info)

        stream.seek(header_chunk.sample_chunk_offset)
        sample_chunk = _read_chunk(stream, HdChunkType.sample)

        stream.seek(header_chunk.sample_set_chunk_offset)
        sample_set_chunk = _read_chunk(stream, HdChunkType.sample_set)

        stream.seek(header_chunk.program_chunk_offset)
        program_chunk = _read_chunk(stream, HdChunkType.program)

        return cls(
            version_chunk=version_chunk,
            vag_info_chunk=vag_info_chunk,
            sample_chunk=sample_chunk,
            sample_set_chunk=sample_set_chunk,
            program_chunk=program_chunk,
            bd_size=header_chunk.bd_size
        )

    def dump(self, stream: BinaryIO):
        start_offset = stream.tell()
        _write_chunk(stream, self.version_chunk)

        header_offset = stream.tell()
        stream.write(b"\x00" * 64)  # this will be filled in later

        vag_info_chunk_offset = stream.tell()
        _write_chunk(stream, self.vag_info_chunk)

        sample_chunk_offset = stream.tell()
        _write_chunk(stream, self.sample_chunk)

        sample_set_chunk_offset = stream.tell()
        _write_chunk(stream, self.sample_set_chunk)

        program_chunk_offset = stream.tell()
        _write_chunk(stream, self.program_chunk)

        end_pos = stream.tell()

        stream.seek(header_offset)
        _write_chunk(stream, HdHeaderChunk(
            hd_size=end_pos - start_offset,
            bd_size=self.bd_size,
            program_chunk_offset=program_chunk_offset,
            sample_set_chunk_offset=sample_set_chunk_offset,
            sample_chunk_offset=sample_chunk_offset,
            vag_info_chunk_offset=vag_info_chunk_offset
        ), length=64)

        stream.seek(end_pos)

    def get_vags(self, bd_stream: BinaryIO) -> List[VagFile]:
        vag_items = self.vag_info_chunk.items
        self.vag_info_chunk.dump(io.BytesIO())
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
