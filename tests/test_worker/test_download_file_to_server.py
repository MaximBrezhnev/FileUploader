from unittest.mock import patch, mock_open, MagicMock
from requests.exceptions import HTTPError

from src.worker import download_file_to_server


@patch("src.worker.requests.get")
@patch("src.worker.open", new_callable=mock_open)
@patch("src.worker.os.path.getsize")
@patch("src.worker._get_db_session_for_task")
@patch("src.worker._update_file_size")
def test_download_file_successfully(
        mock_update_file_size,
        mock_get_db_session_for_task,
        mock_getsize,
        mock_open_file,
        mock_requests_get
):
    file_url = "https://example.com/file.txt"
    file_id = "1234"
    file_path = "/some_way/uploads/file.txt"
    file_size = 1024

    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b'test data']
    mock_requests_get.return_value = mock_response
    mock_getsize.return_value = file_size

    download_file_to_server(file_url=file_url, file_id=file_id, file_path=file_path)

    mock_requests_get.assert_called_once_with(file_url, stream=True)
    mock_open_file.assert_called_once_with(file_path, 'wb')
    mock_getsize.assert_called_once_with(file_path)
    mock_update_file_size.assert_called_once_with(
        mock_get_db_session_for_task.return_value, file_id, file_size
    )


@patch("src.worker.requests.get")
@patch("src.worker._get_db_session_for_task")
@patch("src.worker._delete_nonexistent_file_from_db")
def test_download_file_not_found(
        mock_delete_nonexistent_file_from_db,
        mock_get_db_session_for_task,
        mock_requests_get
):
    file_url = "https://example.com/nonexistent-file.txt"
    file_id = "1234"
    file_path = "/some_way/uploads/nonexistent-file.txt"

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError("File not found")
    mock_requests_get.return_value = mock_response

    download_file_to_server(file_url=file_url, file_id=file_id, file_path=file_path)

    mock_requests_get.assert_called_once_with(file_url, stream=True)
    mock_delete_nonexistent_file_from_db.assert_called_once_with(
        mock_get_db_session_for_task.return_value, file_id
    )

