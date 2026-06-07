import jsonschema

from codex.codexJsonReaderWriter import CodexJsonReaderWriter


def _raiseValidationError(*args, **kwargs):
    raise jsonschema.exceptions.ValidationError("forced validation failure")


def test_save_and_load_round_trip(resolve, tmp_path, test_config):
    test_config.pathToSaveDirectory = str(tmp_path)
    writer = resolve(CodexJsonReaderWriter)

    assert writer.save(["Chicken", "Bear"]) is True
    loaded = writer.load()

    assert sorted(loaded) == ["Bear", "Chicken"]


def test_save_aborts_and_preserves_existing_file_on_validation_error(
    resolve, tmp_path, test_config, monkeypatch
):
    test_config.pathToSaveDirectory = str(tmp_path)
    writer = resolve(CodexJsonReaderWriter)

    # Write a known-good codex first
    writer.save(["Chicken", "Bear"])
    codexPath = tmp_path / "codex.json"
    goodContent = codexPath.read_text()

    # A validation failure must NOT clobber the existing good file
    monkeypatch.setattr(jsonschema, "validate", _raiseValidationError)
    result = writer.save(["Chicken", "Bear", "Apple"])

    assert result is False
    assert codexPath.read_text() == goodContent
