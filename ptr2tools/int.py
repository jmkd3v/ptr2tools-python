import json
from io import BytesIO
from enum import IntEnum
from pathlib import Path
from typing import List, Dict, Optional, BinaryIO
from dataclasses import dataclass


class IntResourceType(IntEnum):
    end = 0
    textures = 1
    sounds = 2
    stage = 3
    red_hat = 4
    blue_hat = 5
    pink_hat = 6
    yellow_hat = 7


resource_type_to_path: Dict[IntResourceType, str] = {
    IntResourceType.textures: "Textures",
    IntResourceType.sounds: "Sounds",
    IntResourceType.stage: "Props",
    IntResourceType.red_hat: "Hats/Red",
    IntResourceType.blue_hat: "Hats/Blue",
    IntResourceType.pink_hat: "Hats/Pink",
    IntResourceType.yellow_hat: "Hats/Yellow"
}


class IntHeader:
    """
    Represents the .INT file's header.
    """

    def __init__(self, stream: BinaryIO):
        self.files: List[IntFile] = []

        magic = int.from_bytes(bytes=stream.read(4), byteorder="little")
        assert magic == 0x44332211, f"magic must be 0x44332211, got {hex(magic)}"

        self.magic: int = magic
        self.file_count: int = int.from_bytes(bytes=stream.read(4), byteorder="little")
        self.resource_type: IntResourceType = IntResourceType(int.from_bytes(bytes=stream.read(4), byteorder="little"))
        self.info_offset: int = int.from_bytes(bytes=stream.read(4), byteorder="little")
        self.relative_contents_offset: int = int.from_bytes(bytes=stream.read(4), byteorder="little")
        self.compressed_size: int = int.from_bytes(bytes=stream.read(4), byteorder="little")

        # there are 8 bytes of null data
        assert stream.read(8) == b'\x00' * 8

        print(self.file_count, self.resource_type, self.info_offset, self.relative_contents_offset)


@dataclass()
class IntFile:
    """
    Represents a file inside of an .INT file.
    """

    name: Optional[str]
    size: Optional[int]
    offset: int


class IntChunk:
    """
    Represents a single chunk in an .INT file.
    """

    def __init__(self, stream: BinaryIO):
        start_position = stream.tell()
        self.files: List[IntFile] = []
        self.header: IntHeader = IntHeader(stream)

        for file_number in range(self.header.file_count):
            self.files.append(IntFile(
                offset=int.from_bytes(bytes=stream.read(4), byteorder="little"),
                name=None,
                size=None
            ))

        stream.seek(start_position + self.header.info_offset)

        for file_number in range(self.header.file_count):
            # this would be the name offset but it sucks so we won't use
            stream.read(4)

            self.files[file_number].size = int.from_bytes(bytes=stream.read(4), byteorder="little")

        # so the contents offset is the point where the file contents start, relative to the info offset
        # we seeked to the info offset and then read 8 bytes for each file (name offset and file size for each)
        # now we want to read the file's filenames, which are after this data and before the contents offset
        # so we can just subtract the file_count * 8 from the contents offset to get the amount of data we want to read
        # plus a ton of extra null bytes, which we strip with .strip(b"\x00")
        file_names = stream.read(self.header.relative_contents_offset - (self.header.file_count * 8))\
            .strip(b"\x00")\
            .decode("ascii")\
            .split("\x00")

        for file_number, file in enumerate(self.files):
            file.name = file_names[file_number]

        # we are now at the contents offset, use tell to get that offset
        self.compressed_contents: bytes = stream.read(self.header.compressed_size)

    def extract(self, path: Path, generate_metadata: bool = True):
        """
        Extracts this chunk to a folder.
        """
        file_metadata = []

        for file in self.files:
            file_path = path / file.name
            with open(file_path, "wb") as fp:
                fp.write(file.contents)

            if generate_metadata:
                file_metadata.append({
                    "name": file.name,
                    "original_size": file.size,
                    "binary_size": len(file.contents)
                })

        if generate_metadata:
            metadata = {
                "files": file_metadata,
                "resource_type": self.header.resource_type.value
            }
            metadata_path = path / "parappa.json"
            with open(metadata_path, "w") as fp:
                json.dump(metadata, fp, indent=2)


class IntContainer:
    """
    Represents an .INT file in a PaRappa The Rapper 2 ISO.
    """

    def __init__(self, stream: BinaryIO):
        self.chunks: List[IntChunk] = []

        while True:
            chunk = IntChunk(stream=stream)
            self.chunks.append(chunk)
            if chunk.header.resource_type == IntResourceType.end:
                break

    def extract(self, path: Path, make_directories: bool = True, generate_metadata: bool = True):
        """
        Extracts this .INT to a folder.
        Each chunk will be a separate subdirectory.
        """
        for chunk in self.chunks:
            chunk_path = path / resource_type_to_path[chunk.header.resource_type]
            if make_directories:
                chunk_path.mkdir(
                    parents=True,
                    exist_ok=True
                )
            chunk.extract(
                path=chunk_path,
                generate_metadata=generate_metadata
            )
