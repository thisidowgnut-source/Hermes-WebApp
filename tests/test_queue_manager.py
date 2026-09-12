import os
import json
import pytest
from scripts.queue_manager import add_to_queue, QUEUE_FILE, BASE_DIR

def test_add_to_queue(tmp_path):
    test_queue = tmp_path / ".queue" / "queue.json"
    post_data = {"brand": "dowgnut", "content": "Hello World", "date": "2026-07-22"}
    
    result = add_to_queue(post_data, queue_file=str(test_queue))
    
    assert result is True
    assert os.path.exists(test_queue)
    with open(test_queue, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["brand"] == "dowgnut"

def test_add_to_queue_append(tmp_path):
    test_queue = tmp_path / ".queue" / "queue.json"
    post_1 = {"brand": "brand1", "content": "First post"}
    post_2 = {"brand": "brand2", "content": "Second post"}
    
    add_to_queue(post_1, queue_file=str(test_queue))
    add_to_queue(post_2, queue_file=str(test_queue))
    
    with open(test_queue, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert len(data) == 2
        assert data[0]["brand"] == "brand1"
        assert data[1]["brand"] == "brand2"

def test_corrupted_queue_backup(tmp_path):
    queue_dir = tmp_path / ".queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    test_queue = queue_dir / "queue.json"
    corrupted_backup = queue_dir / "queue_corrupted.json"
    
    # Write invalid JSON
    with open(test_queue, 'w', encoding='utf-8') as f:
        f.write("{invalid_json: true,")
        
    post_data = {"brand": "dowgnut", "content": "Test"}
    
    with pytest.raises(ValueError, match="Corrupted JSON in queue file"):
        add_to_queue(post_data, queue_file=str(test_queue))
        
    # Verify backup file was created with corrupted content
    assert corrupted_backup.exists()
    with open(corrupted_backup, 'r', encoding='utf-8') as f:
        assert f.read() == "{invalid_json: true,"
        
    # Verify original corrupted file was replaced/moved
    assert not test_queue.exists()

def test_relative_paths():
    assert not os.path.isabs(os.path.relpath(QUEUE_FILE, BASE_DIR))
    assert QUEUE_FILE.endswith(os.path.join(".queue", "queue.json"))

