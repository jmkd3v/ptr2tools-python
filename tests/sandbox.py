with open(r"E:\DATA\ST01GM0.INT", "rb") as file:
    data = file.read()
chunk_splitter = int.to_bytes(0x44332211, 4, "little")
chunks = data.split(chunk_splitter)
print(len(chunks))
print(chunks[1][:32])
