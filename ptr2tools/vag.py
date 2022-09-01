import io
import wave
from enum import IntEnum
from typing import BinaryIO
from dataclasses import dataclass, field

VAG_SAMPLE_BYTES = 14
VAG_SAMPLE_NIBBLE = VAG_SAMPLE_BYTES * 2
VAG_LUT_DECODER = [
    (0.0,           0.0),
    (60.0 / 64.0,   0.0),
    (115.0 / 64.0,  -52.0 / 64.0),
    (98.0 / 64.0,   -55.0 / 64.0),
    (122.0 / 64.0,  -60.0 / 64.0)
]


class VagFlag(IntEnum):
    nothing = 0
    loop_last_block = 1
    loop_region = 2
    loop_end = 3
    loop_first_block = 4
    unk = 5
    loop_start = 6
    playback_end = 7


@dataclass
class VagFile:
    data: bytes = field(repr=False)
    sample_rate: int

    @classmethod
    def load(cls, stream: BinaryIO):
        if stream.read(8) != b"VAGp\x00\x00\x00\x04":
            raise ValueError("invalid start portion")
        stream.seek(4, 1)
        content_length = int.from_bytes(stream.read(4), "big")
        sample_rate = int.from_bytes(stream.read(4), "big")

        stream.seek(28, 1)
        data = stream.read(content_length)
        if len(data) != content_length:
            raise ValueError("ran out of data!")

        return cls(
            data=data,
            sample_rate=sample_rate
        )

    def dump(self, stream: BinaryIO):
        stream.write(b"VAGp\x00\x00\x00\x04")
        stream.write(b"\x00" * 4)
        stream.write(int.to_bytes(len(self.data), 4, "big"))
        stream.write(int.to_bytes(self.sample_rate, 4, "big"))
        stream.write(b"\x00" * 28)
        stream.write(self.data)

    def to_sample_stream(self):
        hist_1, hist_2 = 0.0, 0.0

        in_stream = io.BytesIO(self.data)
        out_stream = io.BytesIO()

        while True:
            decoding_coefficient = in_stream.read(1)[0]
            shift = decoding_coefficient & 0xF
            predict = (decoding_coefficient & 0xF0) >> 4
            flags = in_stream.read(1)[0]
            raw_sample = in_stream.read(14)

            flag_enum = VagFlag(flags)
            if flag_enum == VagFlag.playback_end:
                break

            samples = [0 for _ in range(VAG_SAMPLE_NIBBLE)]
            for j in range(VAG_SAMPLE_BYTES):
                samples[j * 2] = raw_sample[j] & 0xF
                samples[j * 2 + 1] = (raw_sample[j] & 0xF0) >> 4

            for j in range(VAG_SAMPLE_NIBBLE):
                s_predict = min(predict, len(VAG_LUT_DECODER) - 1)

                s = samples[j]

                if s & 0x8:
                    s -= 0x10

                sample = int(
                    ((s << 12) >> shift) +
                    (hist_1 * VAG_LUT_DECODER[s_predict][0]) +
                    (hist_2 * VAG_LUT_DECODER[s_predict][1])
                )

                sample = max(-0x8000, min(sample, 0x7FFF))  # clamp sample
                hist_2 = hist_1
                hist_1 = sample

                out_stream.write(sample.to_bytes(
                    length=2,
                    byteorder="little",
                    signed=True
                ))

        out_stream.seek(0)
        return out_stream

    def dump_wav(self, wav_stream: BinaryIO):
        with wave.open(wav_stream, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit, 2 byte
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(self.to_sample_stream().read())
