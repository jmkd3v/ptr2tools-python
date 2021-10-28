from ptr2tools import get_int_from_path

int_data = get_int_from_path(r"E:\DATA\ST01GM0.INT")
for chunk in int_data.chunks:
    print(chunk.header.resource_type)
