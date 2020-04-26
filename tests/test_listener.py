from unittest import mock

import pytest
import unidiff
import werkzeug

from flask import Flask

app = Flask(__name__)
app.config['WBAPI'] = 'test/api'
app.config['WBSPARQL'] = 'test/sparql'
app.config['WBUSER'] = 'user'
app.config['WBPASS'] = 'pass'
ctx = app.app_context()
ctx.push()

from hercules_sync.git import GitFile, GitPushEventHandler
from hercules_sync.listener import on_push, _extract_ontology_files, _synchronize_files
from hercules_sync.webhook import WebHook


@pytest.fixture
def mocked_req():
    with mock.patch("hercules_sync.webhook.request") as req:
        req.headers = {
            'content-type': 'application/json',
            'X-Hub-Signature': 'sha1=61620b06f590da1915eb1f802f9ea701aea5a4d4',
            'X-Github-Event': 'push'
        }
        req.data = b'{"ref": "head", "before": "001", "after": "002"}'
        yield req

@pytest.fixture
def webhook(app):
    return WebHook(app, endpoint='/postreceive', key='abc')

@mock.patch('hercules_sync.listener._extract_ontology_files')
@mock.patch('hercules_sync.listener._synchronize_files')
@mock.patch.object(GitPushEventHandler, '__init__', lambda x, y: None)
def test_on_push_valid(mock_extract, mock_synchronize):
    res = on_push({})
    assert res == (200, 'Ok')
    mock_extract.assert_called_once()
    mock_synchronize.assert_called_once()

def test_on_push_invalid():
    with pytest.raises(werkzeug.exceptions.NotFound):
        on_push({})

def test_extract_files():
    handler = mock.MagicMock()
    added_file_ttl = mock.MagicMock()
    added_file_txt = mock.MagicMock()
    removed_file = mock.MagicMock()
    added_file_ttl.path = 'myfile.ttl'
    added_file_txt.path = 'myotherfile.txt'
    removed_file.path = 'removed.ttl'

    handler.added_files = [GitFile(added_file_ttl, source_content="", target_content=""),
                           GitFile(added_file_txt, source_content="", target_content="")]
    handler.removed_files = [GitFile(removed_file, source_content="", target_content="")]
    handler.modified_files = []
    assert _extract_ontology_files(handler, 'ttl') == handler.removed_files + [handler.added_files[0]]
    assert _extract_ontology_files(handler, 'txt') == [handler.added_files[1]]

@mock.patch('hercules_sync.triplestore.WikibaseAdapter')
@mock.patch('hercules_sync.triplestore.WikibaseAdapter.__init__', return_value=None)
@mock.patch('hercules_sync.synchronization.GraphDiffSyncAlgorithm')
@mock.patch('hercules_sync.synchronization.OntologySynchronizer')
def test_synchronize(mocked_os, mocked_gds, mocked_wb_init, mocked_wb):
    _synchronize_files([GitFile(mock.MagicMock(), "", "")])
    mocked_wb_init.assert_called_once_with(app.config['WBAPI'], app.config['WBSPARQL'],
        app.config['WBUSER'], app.config['WBPASS'])
