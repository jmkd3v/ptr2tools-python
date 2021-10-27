from ptr2tools import get_int_from_path

int_data = get_int_from_path(r"E:\DATA\ST01GM0.INT")
print(int_data.header.fn_table_size)