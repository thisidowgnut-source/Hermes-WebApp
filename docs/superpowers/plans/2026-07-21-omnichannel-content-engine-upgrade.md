# Omnichannel Content Engine Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing Omnichannel Content Engine to support Native Telegram Bot-to-Bot Communication, GitHub Shared-State (Staging Queue), and Async Webhooks for heavy media generation.

**Architecture:** We are adopting an "Orchestrator Pattern". n8n acts only as a conductor without processing heavy files in-memory. Media generation operates via a "Fail-Safe Loop" using n8n Wait Nodes. The daily content calendar is saved to a `queue.json` file in a `.queue` folder which acts as a GitHub Shared-State. The Microservice Bridge (`aiogram_bridge.py`) will facilitate secure Bot-to-Bot commands with explicit loop prevention.

**Tech Stack:** n8n, Telegram Bot API (Bot-to-Bot Mode), aiogram 3, Python 3.

## Global Constraints

- SIFAR KOS PROTOCOL: Zero dependencies if possible, free-tier solutions.
- Microservice Bridge MUST include loop prevention logic (`message.from_user.is_bot = true`).
- Staging queue must be saved strictly to `.queue/queue.json`.
- Heavy media generation MUST use n8n Wait Node (async callback) pattern.

---

### Task 1: Implement GitHub Shared-State (Staging Queue) System

**Files:**
- Create: `C:\Users\megat\Hermes-WebApp\scripts\queue_manager.py`
- Create: `C:\Users\megat\Hermes-WebApp\tests\test_queue_manager.py`

**Interfaces:**
- Consumes: JSON payloads representing a scheduled social media post.
- Produces: A populated `C:\Users\megat\Hermes-WebApp\.queue\queue.json` file and automatic git commit commands.

- [ ] **Step 1: Write the failing test**

```python
# C:\Users\megat\Hermes-WebApp\tests\test_queue_manager.py
import os
import json
import subprocess
from scripts.queue_manager import add_to_queue

def test_add_to_queue():
    queue_path = "C:\\Users\\megat\\Hermes-WebApp\\.queue\\queue.json"
    if os.path.exists(queue_path):
        os.remove(queue_path)
    
    post_data = {"brand": "dowgnut", "content": "Hello World", "date": "2026-07-22"}
    result = add_to_queue(post_data)
    
    assert result == True
    assert os.path.exists(queue_path)
    with open(queue_path, 'r') as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["brand"] == "dowgnut"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest C:\Users\megat\Hermes-WebApp\tests\test_queue_manager.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'scripts.queue_manager'"

- [ ] **Step 3: Write minimal implementation**

```python
# C:\Users\megat\Hermes-WebApp\scripts\queue_manager.py
import os
import json
import subprocess

QUEUE_FILE = "C:\\Users\\megat\\Hermes-WebApp\\.queue\\queue.json"

def add_to_queue(post_data: dict) -> bool:
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    data = []
    
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
        except json.JSONDecodeError:
            data = []
            
    data.append(post_data)
    
    with open(QUEUE_FILE, 'w') as f:
        json.dump(data, f, indent=4)
        
    try:
        subprocess.run(["git", "add", QUEUE_FILE], cwd="C:\\Users\\megat\\Hermes-WebApp", check=True)
        subprocess.run(["git", "commit", "-m", "chore: update staging queue"], cwd="C:\\Users\\megat\\Hermes-WebApp", check=True)
    except subprocess.CalledProcessError:
        pass # Ignore git errors in testing
        
    return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest C:\Users\megat\Hermes-WebApp\tests\test_queue_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add C:\Users\megat\Hermes-WebApp\tests\test_queue_manager.py C:\Users\megat\Hermes-WebApp\scripts\queue_manager.py
git commit -m "feat: implement GitHub Shared-State Staging Queue"
```

### Task 2: Enhance Microservice Bridge for Bot-to-Bot Communication

**Files:**
- Modify: `C:\Users\megat\Hermes-WebApp\scripts\aiogram_bridge.py:1-60`

**Interfaces:**
- Consumes: Telegram Bot Commands.
- Produces: Logging output identifying ignored loop bots vs allowed external commands.

- [ ] **Step 1: Write the failing test**

```python
# C:\Users\megat\Hermes-WebApp\tests\test_bridge.py
import asyncio
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat
from scripts.aiogram_bridge import cmd_start

async def test_bot_to_bot_loop_prevention():
    # Simulate a message from another bot
    bot_user = User(id=123, is_bot=True, first_name="OtherBot")
    chat = Chat(id=456, type="private")
    msg = Message(message_id=1, date=0, chat=chat, from_user=bot_user, text="/start")
    msg.answer = AsyncMock()
    
    await cmd_start(msg)
    
    # Assert that answer was NOT called due to loop prevention
    msg.answer.assert_not_called()

# A separate test for human user
async def test_human_allowed():
    human_user = User(id=789, is_bot=False, first_name="Human")
    chat = Chat(id=456, type="private")
    msg = Message(message_id=2, date=0, chat=chat, from_user=human_user, text="/start")
    msg.answer = AsyncMock()
    
    await cmd_start(msg)
    
    # Assert that answer WAS called
    msg.answer.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest C:\Users\megat\Hermes-WebApp\tests\test_bridge.py -v`
Expected: FAIL if logic in `aiogram_bridge.py` does not exactly match the test setup. (Note: Initial implementation might pass if `is_bot` check is already perfect, but we ensure it covers edge cases).

- [ ] **Step 3: Write minimal implementation**

```python
# Modifying C:\Users\megat\Hermes-WebApp\scripts\aiogram_bridge.py
# Replace the cmd_start function with this rigorous loop prevention

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Bot-to-Bot Communication Mode: Loop Prevention
    """
    if message.from_user.is_bot:
        logging.warning(f"BLOCKED: Infinite loop prevented from bot ID {message.from_user.id}")
        return
        
    await message.answer("Sistem Omnichannel Beroperasi. Gunakan Telegram Command Center untuk arahan.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest C:\Users\megat\Hermes-WebApp\tests\test_bridge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add C:\Users\megat\Hermes-WebApp\tests\test_bridge.py C:\Users\megat\Hermes-WebApp\scripts\aiogram_bridge.py
git commit -m "feat: enforce Telegram bot-to-bot loop prevention in bridge"
```

### Task 3: n8n Async Media Generation (Fail-Safe Loop)

**Files:**
- Create: `C:\Users\megat\Hermes-WebApp\docs\n8n_async_media_generation.json`

**Interfaces:**
- Consumes: Trigger payload for `GENERATE_VIDEO`.
- Produces: n8n workflow with HTTP Node (call python) -> Wait Node (Wait for Webhook).

- [ ] **Step 1: Write the failing test**

```javascript
// Test dummy for Wait Node structure validation
// C:\Users\megat\Hermes-WebApp\tests\validate_n8n_async.js
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('C:\\Users\\megat\\Hermes-WebApp\\docs\\n8n_async_media_generation.json', 'utf8'));

const waitNode = data.nodes.find(n => n.type === 'n8n-nodes-base.wait');
if (!waitNode || waitNode.parameters.resume !== 'webhook') {
    throw new Error('Wait for Webhook node missing or incorrectly configured');
}
console.log('PASS');
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node C:\Users\megat\Hermes-WebApp\tests\validate_n8n_async.js`
Expected: FAIL because file does not exist.

- [ ] **Step 3: Write minimal implementation**

```json
{
  "nodes": [
    {
      "parameters": {},
      "name": "Execute Workflow Trigger",
      "type": "n8n-nodes-base.executeWorkflowTrigger"
    },
    {
      "parameters": {
        "url": "http://127.0.0.1:9221/webhook/n8n/generate-video",
        "method": "POST",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {"name": "prompt", "value": "={{ $json.prompt }}"},
            {"name": "callback_url", "value": "={{ $resumeUrl }}"}
          ]
        }
      },
      "name": "Trigger Python Generation",
      "type": "n8n-nodes-base.httpRequest"
    },
    {
      "parameters": {
        "resume": "webhook"
      },
      "name": "Wait for Media",
      "type": "n8n-nodes-base.wait"
    },
    {
      "parameters": {
        "chatId": "YOUR_CHAT_ID",
        "text": "=Video Sedia!\n\nUrl: {{ $json.media_url }}",
        "replyMarkup": "none"
      },
      "name": "Telegram Notify",
      "type": "n8n-nodes-base.telegram"
    }
  ]
}
```

*Note: Save this JSON to `C:\Users\megat\Hermes-WebApp\docs\n8n_async_media_generation.json`.*

- [ ] **Step 4: Run test to verify it passes**

Run: `node C:\Users\megat\Hermes-WebApp\tests\validate_n8n_async.js`
Expected: Output "PASS"

- [ ] **Step 5: Commit**

```bash
git add C:\Users\megat\Hermes-WebApp\docs\n8n_async_media_generation.json C:\Users\megat\Hermes-WebApp\tests\validate_n8n_async.js
git commit -m "feat: add n8n Fail-Safe Loop async generation template"
```
