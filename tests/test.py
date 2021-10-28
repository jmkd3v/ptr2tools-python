from ptr2tools import get_int_from_path

int_data = get_int_from_path(r"E:\DATA\ST01GM0.INT")
for chunk in int_data.chunks:
    print(f"Chunk {chunk.header.resource_type.name}")
    for file in chunk.files:
        print(f"\tFile {file.name}")
        print(f"\t\tSize {file.size}")
        print(f"\t\tBinarySize {len(file.compressed_contents)}")
