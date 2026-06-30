import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from src.gateways.dlq_replay import replay_dlq


def test_replay_dlq_no_file():
    with patch("os.path.exists", return_value=False):
        with pytest.raises(SystemExit):
            replay_dlq()


def test_replay_dlq_success_and_poison():
    # Setup mock file content with one normal message and one poisoned/security-flagged message
    normal_entry = {
        "source": "agent_a",
        "target": "agent_b",
        "payload": {"msg": "hello"},
        "reason": "Temporary Timeout",
    }
    poisoned_entry = {
        "source": "agent_c",
        "target": "agent_d",
        "payload": {"msg": "malicious"},
        "reason": "Poisoning detected",
    }

    file_content = json.dumps(normal_entry) + "\n" + json.dumps(poisoned_entry) + "\n"

    mock_redis = MagicMock()

    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=file_content)
    ) as mock_file, patch("redis.Redis.from_url", return_value=mock_redis):
        replay_dlq()

        # Verify redis LPUSH was called once with the normal message
        assert mock_redis.lpush.call_count == 1
        call_args = mock_redis.lpush.call_args
        assert call_args[0][0] == "sentinel.in"
        pushed_payload = json.loads(call_args[0][1])
        assert pushed_payload["source"] == "agent_a"
        assert pushed_payload["payload"] == {"msg": "hello"}

        # Verify the file was written back with the poisoned/skipped message
        # Since we use mock_open, we can check write calls
        write_handle = mock_file()
        written_data = "".join(call[0][0] for call in write_handle.write.call_args_list)
        assert "Poisoning detected" in written_data
        assert "Temporary Timeout" not in written_data
