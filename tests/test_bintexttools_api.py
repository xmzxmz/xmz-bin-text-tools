import json

from bintexttools import bin2text, text2bin


def test_bin2text_and_text2bin_round_trip(tmp_path):
    original_data = bytes(range(32)) + b"Hello bintexttools!"
    input_bin = tmp_path / "input.bin"
    text_output = tmp_path / "output.txt"
    restored_bin = tmp_path / "restored.bin"

    input_bin.write_bytes(original_data)

    bin2text(str(input_bin), str(text_output), format="HEX", show_header=False)
    assert text_output.exists()
    assert text_output.read_text().strip() != ""

    text2bin(str(text_output), str(restored_bin), format="HEX")
    assert restored_bin.exists()
    assert restored_bin.read_bytes() == original_data


def test_text2bin_uses_header_metadata(tmp_path):
    original_data = b"\x00\xffHEADER\x10"
    input_bin = tmp_path / "input.bin"
    text_with_header = tmp_path / "output_with_header.txt"
    restored_bin = tmp_path / "restored.bin"

    input_bin.write_bytes(original_data)

    bin2text(str(input_bin), str(text_with_header), format="HEX", show_header=True)
    contents = text_with_header.read_text()
    assert "<<< HEADER" in contents and ">>> HEADER" in contents
    header_segment = contents.split("<<< HEADER", 1)[1].split(">>> HEADER", 1)[0]
    header_lines = [line for line in header_segment.splitlines() if line.strip()]
    json_start = next(i for i, line in enumerate(header_lines) if line.strip().startswith("{"))
    header_data = json.loads("\n".join(header_lines[json_start:]))
    assert header_data["binFile"]["filename"] == input_bin.name

    text2bin(str(text_with_header), str(restored_bin))
    assert restored_bin.read_bytes() == original_data
