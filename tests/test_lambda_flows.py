"""Tests for the Lambda flow routing and attachment validation."""

import importlib.util
import os
import sys
import types
from unittest.mock import MagicMock

import pytest

HANDLER_PATH = os.path.join('src', 'templevis', 'lambda', 'lambda_handler.py')
BROTHERS_PDF = os.path.join('memory-bank', 'Brothers aug 5.pdf')
SISTERS_PDF = os.path.join('memory-bank', 'Sisters Aug 5.pdf')


@pytest.fixture(scope="module")
def handler():
    """Import lambda_handler with boto3 stubbed out."""
    if 'boto3' not in sys.modules:
        boto3_stub = types.ModuleType('boto3')
        boto3_stub.client = lambda *args, **kwargs: MagicMock()
        sys.modules['boto3'] = boto3_stub

    spec = importlib.util.spec_from_file_location('templevis_lambda_handler', HANDLER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _require(path):
    if not os.path.exists(path):
        pytest.skip(f"Test file not found: {path}")
    return path


def test_determine_flow_uses_key_prefix(handler):
    assert handler.determine_flow('veil/abc123') == handler.FLOW_VEIL
    assert handler.determine_flow('emails/initiatory/abc123') == handler.FLOW_INITIATORY


def test_determine_flow_rejects_unknown_prefix(handler):
    with pytest.raises(handler.PDFValidationError):
        handler.determine_flow('emails/abc123')


def test_initiatory_rejects_too_many_attachments(handler):
    attachments = [(f'/tmp/f{i}.pdf', f'f{i}.pdf') for i in range(handler.MAX_ATTACHMENTS + 1)]

    with pytest.raises(handler.PDFValidationError) as error:
        handler.process_initiatory_flow(attachments, 'msg')

    assert str(handler.MAX_ATTACHMENTS) in str(error.value)


def test_classify_schedule_pdf(handler):
    assert handler.classify_schedule_pdf(_require(BROTHERS_PDF), 'a.pdf') == 'brothers'
    assert handler.classify_schedule_pdf(_require(SISTERS_PDF), 'b.pdf') == 'sisters'


def test_veil_requires_both_schedules(handler):
    _require(BROTHERS_PDF)

    with pytest.raises(handler.PDFValidationError) as error:
        handler.process_veil_flow([(BROTHERS_PDF, 'Brothers aug 5.pdf')], 'msg')

    assert 'sisters schedule' in str(error.value)


def test_veil_rejects_duplicate_schedules(handler):
    _require(BROTHERS_PDF)
    attachments = [
        (BROTHERS_PDF, 'Brothers aug 5.pdf'),
        (BROTHERS_PDF, 'Brothers copy.pdf'),
    ]

    with pytest.raises(handler.PDFValidationError) as error:
        handler.process_veil_flow(attachments, 'msg')

    assert 'duplicate' in str(error.value)


def test_veil_flow_generates_workbook(handler):
    _require(BROTHERS_PDF)
    _require(SISTERS_PDF)

    outputs = handler.process_veil_flow(
        [(BROTHERS_PDF, 'Brothers aug 5.pdf'), (SISTERS_PDF, 'Sisters Aug 5.pdf')],
        'msg',
    )

    assert len(outputs) == 1
    assert os.path.exists(outputs[0])
