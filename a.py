import bencode2

with open("./tests/fixtures/56507.torrent", "rb") as f:
    data = bencode2.bdecode(f.read(), str_key=True)
    data["announce"] = ""
    print(data)
# with open('./tests/fixtures/56507.torrent', 'wb') as f:
#     f.write(bencode2.bencode(data))
