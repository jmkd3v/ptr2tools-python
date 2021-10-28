from pathlib import Path
from ptr2tools import get_int_from_path

int_data = get_int_from_path(r"E:\DATA\ST01GM0.INT")
int_data.extract(Path(r"J:\Development\PTR2 Modding\Beta Extracted INT\c"))
