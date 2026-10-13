import importlib.util
import pathlib


def load_compiler_module() -> object:
    # Load the compiler_octet.py module by path relative to this test file.
    test_dir = pathlib.Path(__file__).resolve().parent
    tools_dir = test_dir.parent
    mod_path = tools_dir / "compiler_octet.py"
    spec = importlib.util.spec_from_file_location("compiler_octet", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def test_roundtrip_basic() -> None:
    module = load_compiler_module()
    OctetCompiler = module.OctetCompiler
    pack_with_header = module.pack_with_header
    unpack_with_header = module.unpack_with_header

    samples = [
        b"Hello World!",
        "Caf\xc3\xa9  \xf0\x9f\x98\x8a".encode("latin-1", errors="ignore"),
        "Espaces    et\nretours\r\n".encode("utf-8"),
        b"\x00\x01\x20\x20\x02ABC",
    ]

    for raw in samples:
        compressed_body, total_bits = OctetCompiler.compress_bytes(raw)
        payload = pack_with_header(compressed_body, total_bits)
        body, bits = unpack_with_header(payload)
        restored = OctetCompiler.decompress_bytes(body, bits)
        assert restored == raw
