# Loctor Builder - User Guide

> **AI-Powered Autonomous Locator Validator & Self-Healing Engine**
> Version 1.0 | February 2026

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Requirements](#2-system-requirements)
3. [Installation](#3-installation)
4. [Quick Start](#4-quick-start)
5. [Understanding the Input Structure](#5-understanding-the-input-structure)
6. [Writing Your First Test Script](#6-writing-your-first-test-script)
7. [Running an Audit](#7-running-an-audit)
8. [Reading Audit Results](#8-reading-audit-results)
9. [Using the Web Dashboard](#9-using-the-web-dashboard)
10. [Switching AI Providers](#10-switching-ai-providers)
11. [Working with the Self-Healing Engine](#11-working-with-the-self-healing-engine)
12. [Git Auto-Commit Workflow](#12-git-auto-commit-workflow)
13. [Sample Test Data Walkthrough](#13-sample-test-data-walkthrough)
14. [Frequently Asked Questions](#14-frequently-asked-questions)

---

## 1. Introduction

Loctor Builder is a **secondary auditor** for web automation scripts. It takes your existing Page Object Model definitions, opens a real browser, and verifies that every single locator (XPath, CSS selector, ID, etc.) actually finds its intended element on the live page.

When a locator is **broken**, Loctor Builder does not simply report it -- it:

1. Captures forensic evidence (screenshots, DOM, CSS).
2. Sends the evidence to an AI model (Gemini, OpenAI, or Claude).
3. Receives 3 new locator candidates from the AI.
4. Tests each candidate live against the page.
5. Picks the best one, updates your source file, and commits the fix.

This entire process is automated and requires zero manual intervention.

### Who Is This For?

- **QA Engineers** who maintain Selenium/Playwright test suites.
- **SDET Teams** who need automated locator maintenance at scale.
- **DevOps/CI Pipelines** that need self-healing test infrastructure.
- **Anyone** tired of fixing broken locators after UI changes.

---

## 2. System Requirements

| Requirement       | Minimum                     | Recommended                |
|-------------------|-----------------------------|----------------------------|
| **OS**            | Windows 10, macOS 12, Ubuntu 20.04 | Windows 11, macOS 14, Ubuntu 22.04 |
| **Python**        | 3.9+                        | 3.11+                      |
| **RAM**           | 4 GB                        | 8 GB+                      |
| **Disk Space**    | 500 MB                      | 2 GB (for screenshots/logs)|
| **Network**       | Internet access required    | Stable broadband            |
| **Git**           | 2.30+                       | Latest                     |
| **Browser**       | Installed by Playwright     | Chromium (default)         |

### API Keys (at least one required)

| Provider       | Model             | How to Get a Key                              |
|----------------|-------------------|-----------------------------------------------|
| Google Gemini  | gemini-2.5-pro    | https://aistudio.google.com/app/apikey        |
| OpenAI         | gpt-4o            | https://platform.openai.com/api-keys          |
| Anthropic      | claude-3.5-sonnet | https://console.anthropic.com/settings/keys   |

---

## 3. Installation

### Step 1: Clone or Download the Project

```bash
cd your-projects-folder
git clone <repository-url> Loctor_Builder
cd Loctor_Builder
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

If your network is slow, install in stages:

```bash
pip install playwright rich flask tinydb click python-dotenv jinja2
pip install flask-socketio gitpython aiohttp aiofiles
pip install openai anthropic google-generativeai
```

### Step 4: Install the Browser

Playwright needs a browser binary. Install Chromium:

```bash
playwright install chromium
```

### Step 5: Configure Your API Key

Copy the environment template and add your key:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` and replace the placeholder with your real key:

```
GEMINI_API_KEY=your_actual_api_key_here
```

> **Security Note:** The `.env` file is listed in `.gitignore` and will never be committed to version control. Never share your API keys.

### Step 5 (Alternative): Edit config.json Directly

If you prefer not to use `.env`, you can place your key directly in `config.json`:

```json
"gemini": {
  "model": "gemini-2.5-pro",
  "api_key": "your_actual_api_key_here"
}
```

### Verify Installation

```bash
python main.py status
```

You should see a table displaying your configuration with the active provider, models, and settings.

---

## 4. Quick Start

Run a pre-built sample in 3 commands:

```bash
# 1. Validate known-good locators (expect all PASSED)
python main.py audit input/scripts/01_herokuapp_login.json

# 2. Run with broken locators to see AI healing in action
python main.py audit input/scripts/02_herokuapp_broken_locators.json

# 3. Run the multi-page audit
python main.py audit input/scripts/03_herokuapp_multi_page.json
```

Or use the automated test runner:

```bash
python test_runner.py --test quick
```

---

## 5. Understanding the Input Structure

The project expects input organized in this folder structure:

```
input/
├── scripts/              <-- Your test script JSON files go here
│   ├── 01_herokuapp_login.json
│   ├── 02_herokuapp_broken_locators.json
│   ├── 03_herokuapp_multi_page.json
│   └── 04_herokuapp_mixed_strategies.json
│
├── page_objects/         <-- The actual source code files referenced by scripts
│   ├── login_page.py
│   ├── login_page_broken.py
│   ├── checkboxes_page.py
│   ├── dropdown_page.py
│   ├── form_auth_page.py
│   └── mixed_strategies.py
│
└── test_configs/         <-- Preset configurations for different run profiles
    ├── quick_validation.json
    ├── full_healing_test.json
    └── comprehensive_suite.json
```

### What Each Folder Contains

| Folder              | Purpose |
|---------------------|---------|
| `input/scripts/`    | JSON files that define **what** to audit: which URLs, which elements, and which locators to check. |
| `input/page_objects/`| The **actual source code** (Python, Java, JS, etc.) that contains the locator strings. The system modifies these files when healing. |
| `input/test_configs/`| Optional preset profiles that bundle a script with specific settings overrides. |

---

## 6. Writing Your First Test Script

A test script is a JSON file that tells Loctor Builder what to audit.

### Minimal Example

Create a file `input/scripts/my_first_test.json`:

```json
{
  "name": "My First Test",
  "base_url": "https://the-internet.herokuapp.com",
  "pages": [
    {
      "name": "Login Page",
      "url": "/login",
      "elements": [
        {
          "name": "username_field",
          "strategy": "id",
          "value": "username",
          "intent": "The username text input"
        }
      ]
    }
  ]
}
```

Run it:

```bash
python main.py audit input/scripts/my_first_test.json
```

### Full Example with All Fields

```json
{
  "name": "Complete Example",
  "base_url": "https://your-app.com",
  "metadata": {
    "author": "Your Name",
    "version": "1.0",
    "description": "Full audit of the login and dashboard pages"
  },
  "pages": [
    {
      "name": "Login Page",
      "url": "/login",
      "description": "User authentication page",
      "elements": [
        {
          "name": "email_input",
          "strategy": "id",
          "value": "email",
          "intent": "Email address input field for login",
          "line_number": 12,
          "file_path": "tests/pages/login_page.py"
        },
        {
          "name": "submit_button",
          "strategy": "css",
          "value": "button[type='submit']",
          "intent": "Form submit button to log in",
          "line_number": 14,
          "file_path": "tests/pages/login_page.py"
        },
        {
          "name": "forgot_password_link",
          "strategy": "xpath",
          "value": "//a[contains(text(),'Forgot')]",
          "intent": "Link to the password recovery page",
          "line_number": 16,
          "file_path": "tests/pages/login_page.py"
        }
      ]
    }
  ]
}
```

### Element Field Reference

| Field         | Required | Type   | Description |
|---------------|----------|--------|-------------|
| `name`        | Yes      | string | A unique identifier for this element. Used in reports and commit messages. |
| `strategy`    | Yes      | string | Locator type. One of: `id`, `css`, `xpath`, `name`, `class_name`, `tag_name`, `link_text`, `partial_link_text`. |
| `value`       | Yes      | string | The actual locator expression (e.g., `#my-btn`, `//div[@class='header']`). |
| `intent`      | No       | string | A human-readable description of what this element is supposed to be. **Greatly improves AI healing accuracy.** |
| `line_number` | No       | int    | Line number in the source file where this locator appears. Enables automatic file updates. |
| `file_path`   | No       | string | Path to the source file. Enables automatic file updates and Git commits. |

> **Tip:** Always include `intent`. When the AI knows the element is supposed to be a "Submit button", it makes dramatically better locator suggestions than when it has to guess from raw HTML alone.

---

## 7. Running an Audit

### Basic Audit

```bash
python main.py audit input/scripts/01_herokuapp_login.json
```

### Audit with Options

```bash
# Use a specific AI provider
python main.py audit input/scripts/02_herokuapp_broken_locators.json --provider claude

# Watch the browser (non-headless mode)
python main.py audit input/scripts/01_herokuapp_login.json --no-headless

# Point to a Git repository for auto-commits
python main.py audit input/scripts/02_herokuapp_broken_locators.json --repo ./my-test-repo

# Use a different config file
python main.py -c my_config.json audit input/scripts/01_herokuapp_login.json
```

### Understanding the Output

When you run an audit, you'll see output like this:

```
╭──────────────────────────────────────────╮
│          Loctor Builder                  │
│  AI-Powered Autonomous Locator Validator │
╰──────────────────────────────────────────╯
Script:   input/scripts/01_herokuapp_login.json
Provider: gemini
Headless: True

Page: Login Page (https://the-internet.herokuapp.com/login)
   PASSED  page_heading (css=h2)
   PASSED  username_input (id=username)
   PASSED  password_input (id=password)
   PASSED  login_button (css=button.radius)
   PASSED  subheader_text (css=h4.subheader)

          Audit Summary
┌──────────────────┬───────┐
│ Metric           │ Value │
├──────────────────┼───────┤
│ Total Elements   │     5 │
│ Passed           │     5 │
│ Healed           │     0 │
│ Failed           │     0 │
│ Success Rate     │ 100.0%│
│ Provider         │ gemini│
│ Duration         │ 0:00:8│
└──────────────────┴───────┘
```

### Status Icons

| Status    | Meaning |
|-----------|---------|
| **PASSED** | Locator found the element successfully with good visibility. |
| **HEALED** | Locator was broken, but the AI found a working replacement. The source file has been updated. |
| **FAILED** | Locator was broken and the AI could not find a replacement after all retry attempts. |
| **SKIPPED** | The page failed to load, so all its elements were skipped. |

---

## 8. Reading Audit Results

After every audit run, a detailed JSON report is saved to `logs/reports/`.

### Report Location

```
logs/reports/audit_HerokuApp Login Flow_20260216_143022.json
```

### Report Structure

```json
{
  "script_name": "HerokuApp Login Flow",
  "start_time": "2026-02-16T14:30:22",
  "end_time": "2026-02-16T14:30:30",
  "total_elements": 5,
  "passed": 4,
  "failed": 0,
  "healed": 1,
  "success_rate": 100.0,
  "ai_provider_used": "gemini",
  "results": [
    {
      "element_name": "username_input",
      "page_name": "Login Page",
      "status": "healed",
      "original_locator": {
        "strategy": "id",
        "value": "txt_username_BROKEN"
      },
      "healed_locator": {
        "locator": {
          "strategy": "id",
          "value": "username"
        },
        "reasoning": "The input field has id='username'",
        "visibility_score": 1.0
      },
      "forensic_evidence": {
        "full_page_screenshot": "./logs/screenshots/..._full_page.png",
        "dom_snapshot_path": "./logs/dom/..._DOM_structure.html"
      }
    }
  ]
}
```

### Forensic Evidence (on Failure/Heal)

When a locator fails, the system saves:

| File                          | Description |
|-------------------------------|-------------|
| `*_full_page.png`            | Full-page screenshot at the time of failure. |
| `*_target_area.png`          | Cropped screenshot of the viewport area. |
| `*_DOM_structure.html`       | Complete HTML source of the page. |

These are stored in `logs/screenshots/` and `logs/dom/`.

---

## 9. Using the Web Dashboard

Launch the real-time monitoring dashboard:

```bash
python main.py dashboard
```

Then open your browser to **http://localhost:5050**.

### Dashboard Features

| Panel               | What It Shows |
|---------------------|---------------|
| **AI Provider**     | Three buttons (Gemini, OpenAI, Claude). Click to switch the active provider instantly. The active provider is highlighted. |
| **Audit Statistics**| Live counters for Total, Passed, Healed, and Failed elements. Updates in real-time as an audit runs. |
| **Settings**        | Toggle auto-commit, headless mode, and adjust retry limit/timeout values. Changes take effect immediately. |
| **Configuration**   | Displays the full config.json (with API keys redacted). |
| **Live Activity Feed** | Scrolling log of every audit event with timestamps and color-coded status. |

> **Note:** The dashboard and the CLI can run simultaneously. Start the dashboard in one terminal, then run an audit from another -- the dashboard will display live results.

---

## 10. Switching AI Providers

You can switch between Gemini, OpenAI, and Claude at any time.

### Via CLI

```bash
# Switch to OpenAI
python main.py switch openai

# Switch to Claude
python main.py switch claude

# Switch back to Gemini
python main.py switch gemini
```

### Via CLI Flag (Per-Run)

```bash
python main.py audit my_script.json --provider claude
```

This switches the provider for that run only.

### Via Web Dashboard

Click the provider button on the dashboard. The change takes effect immediately and persists to `config.json`.

### Via .env File

Set the `ACTIVE_PROVIDER` variable:

```
ACTIVE_PROVIDER=openai
```

### Check Current Provider

```bash
python main.py providers
```

Output:

```
       AI Providers
┌────────┬─────────────────────────┬─────────────────┐
│ Name   │ Model                   │ Status          │
├────────┼─────────────────────────┼─────────────────┤
│ gemini │ gemini-2.5-pro          │ Active          │
│ openai │ gpt-4o                  │ (no API key)    │
│ claude │ claude-3-5-sonnet-20241022 │ (no API key) │
└────────┴─────────────────────────┴─────────────────┘
```

---

## 11. Working with the Self-Healing Engine

### How Healing Works

When an element's locator fails:

1. **Forensic Collection** -- Screenshots, DOM, and CSS are captured.
2. **AI Consultation** -- The broken locator, HTML context, CSS properties, and element intent are sent to the AI.
3. **Candidate Generation** -- The AI returns exactly 3 candidates using different strategies:
   - One **ID-based or attribute-based** locator (most stable).
   - One **CSS selector** locator.
   - One **relative XPath** locator.
4. **Duplicate Check** -- Each candidate is checked against the Known Locators database.
5. **Live Validation** -- Each candidate is tested on the actual page. The system scores its visibility (0.0 to 1.0).
6. **Selection** -- The first validated candidate with the highest visibility score wins.
7. **File Update** -- The old locator in the source code is replaced with the new one, and a comment is added:
   ```python
   # AI-Generated on 2026-02-16: verified via Gemini - The input field has id='username'
   USERNAME_INPUT = (By.ID, "username")
   ```
8. **Git Commit** -- If auto-commit is enabled:
   ```
   [AI-HEAL] Updated locator for object: username_input on page: https://...
   ```

### Retry Logic

If the first AI attempt doesn't produce a valid candidate, the system retries up to `retry_limit` times (default: 3). Each retry makes a fresh AI call.

### Known Locators Database

Located at `data/known_locators.json`, this TinyDB database prevents the same locator from being assigned to two different elements. If the AI suggests a locator that already belongs to another element, it is skipped.

---

## 12. Git Auto-Commit Workflow

### How It Works

1. When a locator is healed and the element has a `file_path` defined, the system:
   - Modifies the source file (replaces the old locator, adds a comment).
   - Stages the file with `git add`.
   - Commits with the message: `[AI-HEAL] Updated locator for object: {name} on page: {url}`.

2. The commit message body includes the AI provider used.

### Enable/Disable Auto-Commit

In `config.json`:

```json
"auto_commit": true    // or false
```

Or via the dashboard toggle.

### Repository Setup

Point to your Git repo when running the audit:

```bash
python main.py audit my_script.json --repo /path/to/my/test-repo
```

If no `--repo` is specified, auto-commit is skipped even if enabled.

---

## 13. Sample Test Data Walkthrough

The project ships with 4 sample scripts and 6 page object files.

### Script 01: Valid Locators

**File:** `input/scripts/01_herokuapp_login.json`
**Purpose:** All 5 locators are correct. Use this to verify the system works.
**Expected Result:** 5/5 PASSED.

### Script 02: Broken Locators (Healing Demo)

**File:** `input/scripts/02_herokuapp_broken_locators.json`
**Purpose:** 2 locators are intentionally broken (`txt_username_BROKEN`, `btn-submit-BROKEN`). 2 are correct.
**Expected Result:** 2 PASSED, 2 HEALED (if AI key is configured).

### Script 03: Multi-Page Navigation

**File:** `input/scripts/03_herokuapp_multi_page.json`
**Purpose:** Navigates 3 different pages (Checkboxes, Dropdown, Login).
**Expected Result:** 6/6 PASSED.

### Script 04: Mixed Locator Strategies

**File:** `input/scripts/04_herokuapp_mixed_strategies.json`
**Purpose:** Uses ID, Name, CSS, and XPath strategies on a single page.
**Expected Result:** 5/5 PASSED.

### Running the Test Suite

```bash
# Run all sample tests
python test_runner.py --test all

# Run just the quick validation
python test_runner.py --test quick

# Run just the healing demo
python test_runner.py --test healing

# Run just the multi-page test
python test_runner.py --test multipage

# Run just the mixed strategies test
python test_runner.py --test mixed
```

---

## 14. Frequently Asked Questions

### Q: Do I need all three AI providers configured?

**No.** You only need one. Set the `active_provider` in `config.json` to whichever provider you have a key for, and configure only that key.

### Q: Can I use this with my own web application?

**Yes.** Create a JSON script that points to your app's URL and lists your elements. See [Section 6](#6-writing-your-first-test-script).

### Q: What happens if the AI can't fix a broken locator?

It will be marked as **FAILED** in the report. The system retries up to `retry_limit` times. You can increase this in `config.json` or try a different AI provider.

### Q: Does the browser need to be visible?

**No.** By default, the browser runs headless (invisible). Use `--no-headless` to watch it in action.

### Q: Can I run this in a CI/CD pipeline?

**Yes.** Use headless mode (default) and provide your API key via environment variables. The audit returns a non-zero exit code on failure.

### Q: What locator strategies are supported?

`id`, `css`, `xpath`, `name`, `class_name`, `tag_name`, `link_text`, `partial_link_text`.

### Q: Where are the logs stored?

| Output              | Location            |
|---------------------|---------------------|
| Screenshots         | `logs/screenshots/` |
| DOM snapshots       | `logs/dom/`         |
| Audit reports (JSON)| `logs/reports/`     |
| Application log     | `logs/loctor_builder.log` |
| Test runner log     | `logs/test_runner.log`    |

### Q: How do I reset the Known Locators database?

Delete the file `data/known_locators.json`. It will be recreated automatically on the next run.

---

*End of User Guide*
