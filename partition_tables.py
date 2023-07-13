import sys
import uuid


def _create_bytes_list(data: str) -> list:
    """Return the hex string grouped in bytes as a list."""
    # This function was created in my Assignment 2 Hexdump
    data_list = []

    for i in range(0, len(data), 2):
        data_list.append(data[i : i + 2])

    return data_list


def _convert_bytes_endian(bytes_list: list[str], num_bytes: int) -> int:
    """Return and convert the endianness of the given bytes to deicmal."""
    str_bytes = "".join(bytes_list)
    temp_hex_str = "0x" + str_bytes
    temp_hex = int(temp_hex_str, 16).to_bytes(num_bytes, "little").hex()
    return int("0x" + temp_hex, 16)


def _calc_sector_end(sector_start: int, total_sectors: int) -> int:
    """Return the end sector given the sector start and size of the sector."""
    return sector_start + total_sectors - 1


def _trim_str(str_to_trim: str) -> str:
    """Return the substring of the given string before first null codepoint."""
    new_str = ""
    for char in str_to_trim:
        null_codepoint = bytes.fromhex("0000").decode("utf-16")
        if char == null_codepoint:
            break
        new_str += char
    return new_str


def parse_mbr(mbr_bytes: bytes) -> list[dict]:
    """Return a list with each element representing an entry in the MBR."""
    entry_list = []
    mbr_hex = _create_bytes_list(mbr_bytes.hex())
    partition_count = 0
    start_byte = 446
    end_byte = 461
    while partition_count < 4:
        entry = {}
        curr_bytes = mbr_hex[start_byte : end_byte + 1]
        if curr_bytes[4] != "00":
            entry["number"] = partition_count
            sector_start = _convert_bytes_endian(curr_bytes[8:12], 4)
            entry["start"] = sector_start
            sector_size = _convert_bytes_endian(curr_bytes[12:16], 4)
            entry["end"] = _calc_sector_end(sector_start, sector_size)
            entry["type"] = hex(int("0x" + curr_bytes[4], 16))
            entry_list.append(entry)
        start_byte += 16
        end_byte += 16
        partition_count += 1
    return entry_list


def parse_gpt(gpt_file, sector_size: int = 512) -> list[dict]:
    """Return a list with each element representing an entry in the GPT."""
    entry_list = []
    gpt_file.seek(sector_size)
    gpt_header = _create_bytes_list(gpt_file.read(sector_size).hex())
    partion_table_start = _convert_bytes_endian(gpt_header[72:80], 8)
    num_entries = _convert_bytes_endian(gpt_header[80:84], 4)
    size_entry = _convert_bytes_endian(gpt_header[84:88], 4)
    gpt_file.seek(sector_size * partion_table_start)
    partion_count = 0
    while partion_count < num_entries:
        entry = {}
        partion = _create_bytes_list(gpt_file.read(size_entry).hex())
        # Check if the current partition is empty
        if "".join(partion) != "0" * 256:
            entry["number"] = partion_count
            entry["start"] = _convert_bytes_endian(partion[32:40], 8)
            entry["end"] = _convert_bytes_endian(partion[40:48], 8)
            type = bytes.fromhex("".join(partion[0:16]))
            entry["type"] = uuid.UUID(bytes_le=type)
            name = bytes.fromhex("".join(partion[56:128]))
            entry["name"] = _trim_str(name.decode("utf-16-le"))
            entry_list.append(entry)
        partion_count += 1
    return entry_list


def main():
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        with open(filename, "rb") as filedes:
            # data = filedes.read()
            # parse_mbr(data)
            parse_gpt(filedes)


if __name__ == "__main__":
    main()
