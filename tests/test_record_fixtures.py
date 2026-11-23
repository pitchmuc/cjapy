"""The fixture scrubber must not keep customer strings."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "record_fixtures", Path(__file__).resolve().parents[1] / "scripts" / "record_fixtures.py"
)
record_fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(record_fixtures)


def test_scrub_replaces_strings_and_keeps_structure():
    response = {
        "content": [
            {"id": "dv_abc", "name": "Acme Web", "owner": {"name": "Jane Doe", "id": 42},
             "type": "string", "hidden": False, "containerNames": ["visitor", "visit"]},
            {"id": "dv_abc", "description": None, "precision": 2},
        ],
        "lastPage": False,
        "number": 0,
    }

    scrubbed = record_fixtures.Scrubber().scrub(response)

    first, second = scrubbed["content"]
    assert first["name"] == "str_2" and first["owner"]["name"] == "str_3"
    assert first["id"] == second["id"] == "str_1"
    assert first["owner"]["id"] == 42 and first["hidden"] is False
    assert first["type"] == "string"
    assert first["containerNames"] == ["visitor", "visit"]
    assert second["description"] is None and second["precision"] == 2
    assert scrubbed["lastPage"] is False and scrubbed["number"] == 0
    assert "Acme" not in repr(scrubbed) and "Jane" not in repr(scrubbed)


def test_scrub_cuts_content_to_max_rows():
    scrubbed = record_fixtures.Scrubber(max_rows=2).scrub({"content": [{"id": n} for n in range(5)]})
    assert scrubbed["content"] == [{"id": 0}, {"id": 1}]


class FakeConnector:
    def __init__(self, responses):
        self.responses = list(responses)
        self.urls = []

    def getData(self, url, *args, **kwargs):
        self.urls.append(url)
        return self.responses.pop(0)


def test_recording_connector_stops_after_the_page_budget():
    pages = [{"content": [{"id": 1}], "lastPage": False}, {"content": [{"id": 2}], "lastPage": False}]
    recorder = record_fixtures.RecordingConnector(FakeConnector(pages), max_pages=1)
    assert recorder.getData("u1") == pages[0]
    assert recorder.getData("u2") == record_fixtures.STOP_PAGE
    assert recorder.responses == [pages[0]]
    assert recorder.connector.urls == ["u1"]


def test_recording_connector_refuses_to_record_an_error():
    error = {"errorCode": "invalid_data", "errorDescription": "bad expansion"}
    recorder = record_fixtures.RecordingConnector(FakeConnector([error]), max_pages=1)
    try:
        recorder.getData("u1")
    except SystemExit as stop:
        assert "invalid_data" in str(stop)
    else:
        raise AssertionError("an error response was recorded")


def test_recording_connector_keeps_pages_as_sent():
    page = {"content": [{"id": 1}], "lastPage": False}
    recorder = record_fixtures.RecordingConnector(FakeConnector([page]), max_pages=1)
    returned = recorder.getData("u1")
    returned["content"] += [{"id": 2}]  # what cjapy's paging loops do
    assert recorder.responses == [{"content": [{"id": 1}], "lastPage": False}]
