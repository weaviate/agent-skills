"""Offline tests for the batching fallback in skills/weaviate/scripts/import.py."""

import importlib.util
import sys
from pathlib import Path

import weaviate

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "weaviate" / "scripts"
sys.path.insert(0, str(SCRIPTS))

# "import.py" is not importable by name (reserved word), so load it by path.
_spec = importlib.util.spec_from_file_location("import_script", SCRIPTS / "import.py")
import_script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(import_script)


class _Batch:
    def __init__(self, stream_error=None):
        self.stream_error = stream_error
        self.used = None

    def stream(self):
        if self.stream_error:
            raise self.stream_error
        self.used = "stream"
        return "STREAM_CM"

    def dynamic(self):
        self.used = "dynamic"
        return "DYNAMIC_CM"


class _Coll:
    def __init__(self, stream_error=None):
        self.batch = _Batch(stream_error)


def test_prefers_streaming_batches_when_supported():
    coll = _Coll()
    assert import_script.open_batch(coll) == "STREAM_CM"
    assert coll.batch.used == "stream"


def test_falls_back_to_dynamic_on_old_servers(capsys):
    err = weaviate.exceptions.WeaviateUnsupportedFeatureError(
        "Server-side batching", "1.30.0", "1.36.0"
    )
    coll = _Coll(stream_error=err)
    assert import_script.open_batch(coll) == "DYNAMIC_CM"
    assert coll.batch.used == "dynamic"
    assert "1.36" in capsys.readouterr().err


def test_other_errors_are_not_swallowed():
    import pytest

    coll = _Coll(stream_error=RuntimeError("boom"))
    with pytest.raises(RuntimeError):
        import_script.open_batch(coll)
