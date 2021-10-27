from typing import BinaryIO, List


class IntFileHeader:
    """
    Represents the .INT file's header.

    Attributes:
        magic: Should be 0x11223344. Present at the start of an INT file.
    """
    def __init__(self, data: bytes):
        self.magic: int = int.from_bytes(bytes=data[:4], byteorder="big")
        self.file_count: int = int.from_bytes(bytes=data[4:8], byteorder="big")
        self.resource_type: int = int.from_bytes(bytes=data[8:12], byteorder="big")
        self.fn_table_offset: int = int.from_bytes(bytes=data[12:16], byteorder="big")
        self.fn_table_size: int = int.from_bytes(bytes=data[16:20], byteorder="big")
        self.lzss_section_size: int = int.from_bytes(bytes=data[20:24], byteorder="big")
        self.unk: List[int] = [
            int.from_bytes(bytes=data[24:28], byteorder="big"),
            int.from_bytes(bytes=data[28:32], byteorder="big"),
        ]


class IntFile:
    """
    Represents an .INT file in a PaRappa The Rapper 2 ISO.
    """
    def __init__(self, fp: BinaryIO):
        self.fp: BinaryIO = fp
        self.header: IntFileHeader = IntFileHeader(
            data=self.fp.read(32)
        )
