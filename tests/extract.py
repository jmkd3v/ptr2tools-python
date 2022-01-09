from pathlib import Path
from ptr2tools import get_int_from_path

int_data = get_int_from_path(r"E:\DATA\ST01GM0.INT")
chunk = int_data.chunks[0]
chunk.extract(Path(r"J:\Development\PTR2 Modding\Beta Extracted INT\z"))