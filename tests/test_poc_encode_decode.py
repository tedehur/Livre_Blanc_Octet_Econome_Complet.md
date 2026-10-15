import tempfile
from tools import octet_compressor as oc


def test_roundtrip_basic(tmp_path):
    sample = 'hello world\nthis is a test\n'
    in_file = tmp_path / 'in.txt'
    out_file = tmp_path / 'in.txt.octet'
    dec_file = tmp_path / 'in.txt.decoded'
    in_file.write_text(sample, encoding='utf-8')

    oc.write_octet_file(str(out_file), sample)
    decoded = oc.decode_from_file(str(out_file))
    assert decoded == sample
