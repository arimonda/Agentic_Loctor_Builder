# Loctor Builder

**AI-Powered Autonomous Locator Validator & Self-Healing Engine**

Loctor Builder acts as a **Secondary Auditor** for AI-generated (or manually written) automation scripts. It navigates your web application, verifies that every object locator (XPath, CSS, ID) is valid, and when a locator fails, uses a multi-model AI interface to self-heal the script, capture forensic evidence, and commit the fix back to the repository.

---

## Features

- **Multi-Model AI Interface** — Supports Google Gemini (Pro 2.5), OpenAI GPT-4o, and Anthropic Claude (3.5 Sonnet). Switch providers at runtime via CLI or dashboard.
- **Automated Forensic Collection** — On failure, captures full-page screenshots, target-area screenshots, DOM snapshots, and computed CSS properties.
- **Self-Healing Engine** — AI generates 3 unique locator strategies (ID-based, CSS, XPath). Each is validated live against the page with visibility scoring.
- **Duplicate Prevention** — Cross-references new locators against a Known Locators database before testing.
- **File Modification** — Automatically updates source files with healed locators and adds documentation comments.
- **Git Integration** — Auto-commits fixes with descriptive messages: `[AI-HEAL] Updated locator for object: {name} on page: {url}`.
- **Web Dashboard** — Real-time monitoring UI with provider switching, settings management, and live activity feed.
- **Rich CLI** — Full-featured command-line interface with colored output and progress tracking.

---

## Project Structure

```
Loctor_Builder/
├── main.py                      # Application entry point
├── cli.py                       # CLI interface (Click)
├── config.json                  # Central configuration
├── requirements.txt             # Python dependencies
│
├── ai/                          # Multi-Model AI Interface
│   ├── base_provider.py         # Abstract AI provider
│   ├── gemini_provider.py       # Google Gemini implementation
│   ├── openai_provider.py       # OpenAI GPT-4o implementation
│   ├── claude_provider.py       # Anthropic Claude implementation
│   └── provider_factory.py      # Factory + runtime switching
│
├── core/                        # Core Engine
│   ├── config_manager.py        # Config management (thread-safe)
│   ├── browser_engine.py        # Playwright browser automation
│   ├── forensic_agent.py        # Screenshot/DOM/CSS capture
│   ├── healing_engine.py        # Self-healing orchestrator
│   ├── locator_validator.py     # Live locator validation
│   ├── known_locators_db.py     # Duplicate prevention (TinyDB)
│   ├── file_modifier.py         # Source code updater
│   ├── git_manager.py           # Git auto-commit
│   ├── script_loader.py         # Script JSON parser
│   └── auditor.py               # Main audit orchestrator
│
├── models/                      # Data Models
│   ├── locator.py               # Locator & candidate models
│   ├── page_object.py           # Page object models
│   └── audit_result.py          # Audit result & forensic models
│
├── ui/                          # Web Dashboard
│   └── dashboard.py             # Flask + SocketIO dashboard
│
├── scripts/                     # Sample Scripts
│   ├── sample_login_test.json   # Valid locators example
│   └── sample_broken_locators.json  # Broken locators (healing demo)
│
└── logs/                        # Output
    ├── screenshots/             # Forensic screenshots
    ├── dom/                     # DOM snapshots
    └── reports/                 # Audit reports (JSON)
```

---

## Installation

### Prerequisites

- Python 3.10+
- Git

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd Loctor_Builder

# Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Configuration

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```

2. Add your API keys to `.env`:
   ```
   GEMINI_API_KEY=your_gemini_key
   OPENAI_API_KEY=your_openai_key
   CLAUDE_API_KEY=your_claude_key
   ```

   Alternatively, set them directly in `config.json`.

---

## Usage

### CLI Commands

```bash
# Run a full audit
python main.py audit scripts/sample_login_test.json

# Run with a specific AI provider
python main.py audit scripts/sample_broken_locators.json --provider claude

# Run with visible browser (non-headless)
python main.py audit scripts/sample_login_test.json --no-headless

# Specify a Git repo for auto-commits
python main.py audit scripts/sample_login_test.json --repo /path/to/your/repo

# Switch the active AI provider
python main.py switch openai

# View current configuration
python main.py status

# List all providers
python main.py providers

# Launch the web dashboard
python main.py dashboard
```

### Programmatic Usage

```python
import asyncio
from main import run_audit

report = asyncio.run(run_audit(
    script_path="scripts/sample_login_test.json",
    provider="gemini"
))

print(f"Success rate: {report.success_rate}%")
print(f"Healed: {report.healed} elements")
```

---

## Script Format

Automation scripts are JSON files defining pages and their elements:

```json
{
  "name": "My Test Suite",
  "base_url": "https://example.com",
  "pages": [
    {
      "name": "Login Page",
      "url": "/login",
      "elements": [
        {
          "name": "username_input",
          "strategy": "id",
          "value": "username",
          "intent": "Username text input field",
          "line_number": 15,
          "file_path": "tests/pages/login_page.py"
        }
      ]
    }
  ]
}
```

### Element Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier for the element |
| `strategy` | Yes | Locator strategy: `id`, `css`, `xpath`, `name`, `class_name` |
| `value` | Yes | The locator expression |
| `intent` | No | Description of what the element is (helps AI healing) |
| `line_number` | No | Line number in source file (for auto-update) |
| `file_path` | No | Path to source file (for auto-update and git commit) |

---

## Configuration (config.json)

```json
{
  "active_provider": "gemini",
  "providers": {
    "gemini": { "model": "gemini-2.5-pro", "api_key": "..." },
    "openai": { "model": "gpt-4o", "api_key": "..." },
    "claude": { "model": "claude-3-5-sonnet-20241022", "api_key": "..." }
  },
  "settings": {
    "screenshot_path": "./logs/screenshots",
    "auto_commit": true,
    "retry_limit": 3,
    "validation_timeout": 5000,
    "headless": true,
    "browser": "chromium",
    "dashboard_port": 5050
  }
}
```

---

## Execution Flow

```
1. INITIALIZE ─── Load config.json, start browser

2. For each PAGE in script:
   │
   ├── NAVIGATE to page URL
   │
   └── For each ELEMENT on page:
       │
       ├── VERIFY ─── driver.find(element.locator)
       │   ├── SUCCESS ──▶ Mark as PASSED ✓
       │   └── FAILURE ──▶ Trigger HEALING ▼
       │
       ├── COLLECT ─── Full-page screenshot
       │              Target area screenshot
       │              DOM structure (HTML)
       │              Computed CSS properties
       │
       ├── CONSULT ─── Send to AI (Gemini/OpenAI/Claude):
       │              • Broken locator
       │              • HTML snippet + CSS
       │              • Element intent
       │              • Screenshot (vision models)
       │
       ├── ITERATE ─── AI returns 3 candidates: L₁, L₂, L₃
       │              Check each against Known Locators DB
       │              Test each on live page
       │              Score by visibility
       │
       └── FINALIZE ── Update source file with working Lₙ
                       Add AI-Generated comment
                       Git commit: [AI-HEAL] Updated locator...

3. REPORT ─── Save full audit report as JSON
```

---

## Web Dashboard

Launch with `python main.py dashboard` and open `http://localhost:5050`.

Features:
- **Provider Switching** — Click to switch between Gemini, OpenAI, and Claude in real-time
- **Live Statistics** — Watch passed/healed/failed counts update in real-time
- **Settings Panel** — Toggle auto-commit, headless mode, adjust retry limits and timeouts
- **Activity Feed** — Live log of all audit events with color-coded status

---

## License

MIT
