import pytest
from unittest.mock import AsyncMock, patch
from quotexapi.http.qx_pin_getter import QuotexPinGetter

@pytest.mark.asyncio
async def test_get_pin_functional():
    mock_mail_browser = AsyncMock()
    mock_mail_browser.get_latest_email_from_sender.return_value = "mock_email"
    mock_mail_browser.get_email_attachments.side_effect = [["mock_body"]]
    mock_pin_getter = QuotexPinGetter({"quotex_email": "test@example.com"}, attempts=1)
    mock_pin_getter.mail_browser = mock_mail_browser
    mock_pin_getter.parse_email_for_pin.return_value = "123456"

    pin_code = await mock_pin_getter.get_pin()

    assert pin_code == "123456"

@patch('asyncio.sleep')
@pytest.mark.asyncio
async def test_get_pin_with_no_pin_functional(mock_sleep):
    mock_mail_browser = AsyncMock()
    mock_mail_browser.get_latest_email_from_sender.return_value = None
    mock_pin_getter = QuotexPinGetter({"quotex_email": "test@example.com"}, attempts=1)
    mock_pin_getter.mail_browser = mock_mail_browser
    mock_pin_getter.parse_email_for_pin.return_value = None

    pin_code = await mock_pin_getter.get_pin()

    assert pin_code is None