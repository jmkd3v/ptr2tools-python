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

        # the info_offset must be +4 to work with this scheme
        relative_info_offset = self.header.info_offset + 4
        offsets_data: bytes = data[32:relative_info_offset]
        info_data: bytes = data[relative_info_offset:relative_info_offset + self.header.contents_offset]
        contents_data: bytes = data[relative_info_offset + self.header.contents_offset:]

        offsets: List[int] = []
        infos: List[Tuple[int, int]] = []

        for offset_position in range(
            0,  # start at 0
            len(offsets_data),  # end at the offset length
            offsets_size  # split into chunks of 4
        ):
            # To ensure we don't mess up the offsets
            # we'll break when the offset goes *down* from the one we saw last
            offset: int = int.from_bytes(
                bytes=offsets_data[offset_position:offset_position + offsets_size],
                byteorder="little"
            )

            try:
                if offset <= offsets[len(offsets)-1]:
                    # we're past the bounds...
                    break
            except IndexError:
                # catch IndexErrors and drop them
                pass

            offsets.append(
                int.from_bytes(
                    bytes=offsets_data[offset_position:offset_position + offsets_size],
                    byteorder="little"
                )
            )

        for info_position in range(
            0,
            len(info_data),
            name_offsets_size
        ):
            if len(infos) >= len(offsets):
                # cleanup weird overlap.
                break

            name_offset: int = int.from_bytes(
                bytes=info_data[info_position:info_position + offsets_size],
                byteorder="little"
            )

            compressed_size: int = int.from_bytes(
                bytes=info_data[info_position + offsets_size:info_position + (offsets_size * 2)],
                byteorder="little"
            )

            try:
                if name_offset <= infos[len(infos)-1][0]:
                    # we're past the bounds...
                    break
            except IndexError:
                # catch IndexErrors and drop them
                pass

            infos.append((name_offset, compressed_size))

        print(len(offsets), offsets)
        print(len(infos), infos)


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
