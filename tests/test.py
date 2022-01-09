from ptr2tools import IntContainer

with open(r"E:\DATA\ST01GM0.INT", "rb") as file:
    int_container = IntContainer(file)

for chunk in int_container.chunks:
    print(f"Chunk {chunk.header.resource_type.name}")
    print(f"\tCompressed contents size: {len(chunk.compressed_contents)}")
    print("\tFiles:")
    for file in chunk.files:
        print(f"\t\tFile {file}")
