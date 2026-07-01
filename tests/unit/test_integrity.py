import os
import json
from src.antigravity.integrity import MerkleTree, verify_chain


def test_merkle_tree():
    logs = ['{"a": 1}', '{"b": 2}', '{"c": 3}']
    tree = MerkleTree(logs)
    root = tree.root
    assert isinstance(root, str)
    assert len(root) == 64


def test_verify_chain_success(tmp_path):
    from unittest.mock import patch

    mock_base = str(tmp_path)
    target_dir = os.path.join(mock_base, "logs")
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, "agent_decisions.json")
    with open(target_file, "w") as f:
        f.write(json.dumps([{"Body": "test1"}]))

    with patch("os.getcwd", return_value=mock_base):
        # verify_chain just prints, so it shouldn't crash
        verify_chain()


def test_verify_chain_no_file(tmp_path):
    from unittest.mock import patch

    with patch("os.getcwd", return_value=str(tmp_path)):
        verify_chain()
