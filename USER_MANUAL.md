# Loctor Builder - User Manual

> **Technical Reference & Operations Manual**
> Version 1.0 | February 2026

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Module Reference](#2-module-reference)
3. [Configuration Reference](#3-configuration-reference)
4. [CLI Command Reference](#4-cli-command-reference)
5. [API Reference (Programmatic Usage)](#5-api-reference-programmatic-usage)
6. [Input Script Specification](#6-input-script-specification)
7. [AI Provider Details](#7-ai-provider-details)
8. [Forensic Evidence Specification](#8-forensic-evidence-specification)
9. [Self-Healing Engine Internals](#9-self-healing-engine-internals)
10. [Locator Validation & Scoring](#10-locator-validation--scoring)
11. [File Modification Rules](#11-file-modification-rules)
12. [Git Integration Specification](#12-git-integration-specification)
13. [Web Dashboard API Reference](#13-web-dashboard-api-reference)
14. [Data Models Reference](#14-data-models-reference)
15. [Output & Reporting Specification](#15-output--reporting-specification)
16. [Logging Configuration](#16-logging-configuration)
17. [Error Handling & Troubleshooting](#17-error-handling--troubleshooting)
18. [Security Considerations](#18-security-considerations)
19. [Performance Tuning](#19-performance-tuning)
20. [Extending the System](#20-extending-the-system)

---

## 1. System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           LOCTOR BUILDER                                │
│                                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────────────────┐   │
│  │  CLI /   │───>│   Auditor    │───>│      Browser Engine         │   │
│  │ Dashboard │    │ (Orchestrator)│    │      (Playwright)          │   │
│  └──────────┘    └──────┬───────┘    └──────────┬──────────────────┘   │
│                         │                        │                      │
│                         v                        v                      │
│               ┌─────────────────┐    ┌──────────────────────┐          │
│               │  Healing Engine │    │   Forensic Agent     │          │
│               │                 │    │  - Screenshots       │          │
│               │  ┌───────────┐  │    │  - DOM Capture       │          │
│               │  │ AI Provider│  │    │  - CSS Extraction    │          │
│               │  │  Factory   │  │    └──────────────────────┘          │
│               │  │  ┌──────┐ │  │                                      │
│               │  │  │Gemini│ │  │    ┌──────────────────────┐          │
│               │  │  │OpenAI│ │  │    │  Locator Validator   │          │
│               │  │  │Claude│ │  │───>│  - Live Testing      │          │
│               │  │  └──────┘ │  │    │  - Visibility Score  │          │
│               │  └───────────┘  │    │  - Duplicate Check   │          │
│               └─────────┬───────┘    └──────────────────────┘          │
│                         │                                               │
│                         v                                               │
│               ┌─────────────────┐    ┌──────────────────────┐          │
│               │  File Modifier  │───>│    Git Manager       │          │
│               │  - Find & Replace│    │  - Stage & Commit   │          │
│               │  - Add Comment  │    │  - [AI-HEAL] message │          │
│               └─────────────────┘    └──────────────────────┘          │
│                                                                         │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────────────────┐  │
│  │ Config       │  │ Script Loader  │  │ Known Locators DB (TinyDB) │  │
│  │ Manager      │  │ (JSON Parser)  │  │                            │  │
│  └──────────────┘  └────────────────┘  └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Execution Flow (Step-by-Step)

```
START
 │
 ├─1─ ConfigManager loads config.json and .env overrides
 ├─2─ ScriptLoader parses the input JSON into PageObject models
 ├─3─ BrowserEngine launches Chromium via Playwright
 │
 ├─4─ FOR EACH Page in script:
 │     ├── Navigate to base_url + page.url
 │     │
 │     └── FOR EACH Element on page:
 │          │
 │          ├── BrowserEngine.find_element(locator)
 │          │    ├── FOUND + visibility >= 0.3 ──> Status: PASSED
 │          │    │
 │          │    └── NOT FOUND ──> Trigger Healing:
 │          │         │
 │          │         ├─A─ ForensicAgent.collect_evidence()
 │          │         │     ├── Full-page screenshot
 │          │         │     ├── Target area screenshot
 │          │         │     ├── DOM snapshot (HTML)
 │          │         │     └── Surrounding elements CSS
 │          │         │
 │          │         ├─B─ AIProvider.generate_locators()
 │          │         │     ├── Sends: broken locator, HTML, CSS, intent, screenshot
 │          │         │     └── Returns: 3 candidates [{strategy, value, reasoning, confidence}]
 │          │         │
 │          │         ├─C─ LocatorValidator.validate_candidates()
 │          │         │     ├── Check each against KnownLocatorsDB
 │          │         │     ├── Test each on live page
 │          │         │     ├── Score visibility (0.0 - 1.0)
 │          │         │     └── Select best validated candidate
 │          │         │
 │          │         ├─D─ IF candidate selected:
 │          │         │     ├── FileModifier.update_locator_in_file()
 │          │         │     ├── GitManager.commit_heal()
 │          │         │     └── Status: HEALED
 │          │         │
 │          │         └─E─ IF no candidate works (after retry_limit attempts):
 │          │               └── Status: FAILED
 │          │
 │          └── Append result to AuditReport
 │
 ├─5─ BrowserEngine.stop()
 ├─6─ Save AuditReport JSON to logs/reports/
 └─7─ Display summary table
 │
END
```

---

## 2. Module Reference

### Directory: `ai/`

| Module               | Class / Function       | Purpose |
|----------------------|------------------------|---------|
| `base_provider.py`   | `BaseAIProvider`       | Abstract base class. Defines the `generate_locators()` and `analyze_element()` interfaces. Contains the shared prompt template and image encoding utility. |
| `gemini_provider.py` | `GeminiProvider`       | Google Gemini implementation using `google-generativeai`. Supports multimodal input (text + image). |
| `openai_provider.py` | `OpenAIProvider`       | OpenAI GPT-4o implementation using the `openai` async client. Supports vision via base64 images. |
| `claude_provider.py` | `ClaudeProvider`       | Anthropic Claude implementation using the `anthropic` async client. Supports vision via base64 images. |
| `provider_factory.py`| `ProviderFactory`      | Factory pattern that creates and caches provider instances based on config. Supports runtime switching. |

### Directory: `core/`

| Module                | Class / Function       | Purpose |
|-----------------------|------------------------|---------|
| `config_manager.py`   | `ConfigManager`        | Singleton configuration manager. Thread-safe. Loads `config.json`, applies `.env` overrides, supports runtime updates with change callbacks. |
| `browser_engine.py`   | `BrowserEngine`        | Playwright browser wrapper. Manages lifecycle (start/stop), navigation, element finding, visibility scoring, screenshot capture, DOM/CSS extraction. |
| `forensic_agent.py`   | `ForensicAgent`        | Collects all forensic evidence when a locator fails: full-page screenshot, target-area screenshot, DOM snapshot, CSS properties. |
| `healing_engine.py`   | `HealingEngine`        | Orchestrates the full healing cycle: collect evidence, consult AI, validate candidates, select best. Implements retry logic. |
| `locator_validator.py`| `LocatorValidator`     | Tests AI-generated candidates on the live page. Calculates visibility scores. Checks for duplicates. Builds `LocatorCandidateList` from AI output. |
| `known_locators_db.py`| `KnownLocatorsDB`     | TinyDB-backed database for duplicate prevention. Stores all known locators with their object names and source. |
| `file_modifier.py`    | `FileModifier`         | Reads source files, finds the old locator string, replaces it with the healed one, and adds an AI-Generated comment. |
| `git_manager.py`      | `GitManager`           | GitPython wrapper. Initializes repos, stages files, and creates `[AI-HEAL]` commits. |
| `script_loader.py`    | `load_script()`        | Parses input JSON files into typed `AutomationScript` / `PageObject` / `PageElement` data models. |
| `auditor.py`          | `Auditor`              | The top-level orchestrator. Manages the complete audit workflow. Supports progress callbacks. Saves JSON reports. |

### Directory: `models/`

| Module             | Classes                  | Purpose |
|--------------------|--------------------------|---------|
| `locator.py`       | `Locator`, `LocatorCandidate`, `LocatorCandidateList`, `LocatorStrategy` (enum), `LocatorStatus` (enum) | Data models for locators and healing candidates. |
| `page_object.py`   | `PageElement`, `PageObject`, `AutomationScript` | Data models for the page object hierarchy. |
| `audit_result.py`  | `ForensicEvidence`, `ElementAuditResult`, `AuditReport`, `AuditStatus` (enum) | Data models for audit results and forensic evidence. |

### Directory: `ui/`

| Module          | Function / Class     | Purpose |
|-----------------|----------------------|---------|
| `dashboard.py`  | `create_app(config)` | Creates a Flask + SocketIO application with a dark-themed real-time dashboard. Returns `(app, socketio)`. |

### Root Files

| File             | Purpose |
|------------------|---------|
| `main.py`        | Application entry point. Provides both `main()` for CLI and `run_audit()` for programmatic use. |
| `cli.py`         | Click-based CLI with commands: `audit`, `switch`, `status`, `providers`, `dashboard`. |
| `test_runner.py` | Automated test suite runner with 4 predefined tests and JSON report output. |
| `config.json`    | Central configuration file. |
| `.env`           | Environment variables (API keys). Not committed to Git. |

---

## 3. Configuration Reference

### config.json - Complete Field Reference

```json
{
  "active_provider": "<string>",
  "providers": { ... },
  "settings": { ... }
}
```

#### Top-Level Fields

| Field             | Type   | Description |
|-------------------|--------|-------------|
| `active_provider` | string | Which AI provider to use. One of: `gemini`, `openai`, `claude`. |
| `providers`       | object | Configuration for each AI provider. |
| `settings`        | object | Application settings. |

#### Provider Configuration

Each provider has:

| Field     | Type   | Description |
|-----------|--------|-------------|
| `model`   | string | The model identifier to use. |
| `api_key` | string | The API key. Can be overridden by environment variables. |

#### Settings Fields

| Field                | Type    | Default                     | Description |
|----------------------|---------|-----------------------------|-------------|
| `screenshot_path`    | string  | `"./logs/screenshots"`      | Directory for forensic screenshots. |
| `dom_capture_path`   | string  | `"./logs/dom"`              | Directory for DOM snapshot files. |
| `auto_commit`        | boolean | `true`                      | Whether to auto-commit healed locators to Git. |
| `retry_limit`        | integer | `3`                         | Maximum number of AI healing attempts per element. |
| `validation_timeout` | integer | `5000`                      | Timeout in milliseconds for finding elements. Navigation timeout is 3x this value. |
| `headless`           | boolean | `true`                      | Run the browser without a visible window. |
| `browser`            | string  | `"chromium"`                | Browser engine. Options: `chromium`, `firefox`, `webkit`. |
| `viewport_width`     | integer | `1920`                      | Browser viewport width in pixels. |
| `viewport_height`    | integer | `1080`                      | Browser viewport height in pixels. |
| `known_locators_db`  | string  | `"./data/known_locators.json"` | Path to the TinyDB database file. |
| `log_level`          | string  | `"INFO"`                    | Logging level. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `dashboard_port`     | integer | `5050`                      | Port for the web dashboard. |

### Environment Variable Overrides

| Variable          | Overrides                       |
|-------------------|---------------------------------|
| `GEMINI_API_KEY`  | `providers.gemini.api_key`      |
| `OPENAI_API_KEY`  | `providers.openai.api_key`      |
| `CLAUDE_API_KEY`  | `providers.claude.api_key`      |
| `ACTIVE_PROVIDER` | `active_provider`               |
| `HEADLESS`        | `settings.headless` (true/false)|
| `BROWSER`         | `settings.browser`              |

Environment variables always take precedence over `config.json` values.

---

## 4. CLI Command Reference

### Global Options

```
python main.py [OPTIONS] COMMAND [ARGS]
```

| Option           | Short | Default       | Description |
|------------------|-------|---------------|-------------|
| `--config PATH`  | `-c`  | `config.json` | Path to the configuration file. |

### Command: `audit`

Run the locator audit on an automation script.

```
python main.py audit [OPTIONS] SCRIPT_PATH
```

| Argument/Option        | Required | Default  | Description |
|------------------------|----------|----------|-------------|
| `SCRIPT_PATH`          | Yes      | --       | Path to the JSON script file. |
| `--repo PATH` / `-r`   | No       | None     | Path to the Git repository for auto-commits. |
| `--provider NAME` / `-p`| No      | Config   | Override the AI provider (`gemini`, `openai`, `claude`). |
| `--headless`           | No       | Config   | Run browser in headless mode. |
| `--no-headless`        | No       | --       | Run browser with visible window. |

**Exit Codes:**
- `0`: Audit completed (even if some elements failed).
- `1`: Fatal error (config not found, script not found, browser crash).

### Command: `switch`

Switch the active AI provider. The change is persisted to `config.json`.

```
python main.py switch PROVIDER
```

| Argument   | Values                    |
|------------|---------------------------|
| `PROVIDER` | `gemini`, `openai`, `claude` |

### Command: `status`

Display the current configuration in a formatted table.

```
python main.py status
```

### Command: `providers`

List all configured AI providers with their models and status.

```
python main.py providers
```

### Command: `dashboard`

Launch the web-based monitoring dashboard.

```
python main.py dashboard
```

Dashboard runs on the port specified in `settings.dashboard_port` (default: 5050).

---

## 5. API Reference (Programmatic Usage)

### `run_audit()`

The primary programmatic entry point.

```python
from main import run_audit
import asyncio

report = asyncio.run(run_audit(
    script_path="input/scripts/01_herokuapp_login.json",
    config_path="config.json",         # optional
    repo_path="/path/to/git/repo",     # optional
    provider="gemini",                 # optional
))
```

**Parameters:**

| Parameter      | Type            | Default        | Description |
|----------------|-----------------|----------------|-------------|
| `script_path`  | `str`           | --             | Path to the JSON script file. **Required.** |
| `config_path`  | `str`           | `"config.json"`| Path to the config file. |
| `repo_path`    | `Optional[str]` | `None`         | Git repo path for auto-commits. |
| `provider`     | `Optional[str]` | `None`         | Override the AI provider. |

**Returns:** `AuditReport` object.

### `AuditReport` Properties

| Property        | Type    | Description |
|-----------------|---------|-------------|
| `script_name`   | `str`   | Name of the audited script. |
| `total_elements` | `int`  | Total number of elements audited. |
| `passed`        | `int`   | Elements that passed validation. |
| `healed`        | `int`   | Elements that were healed by AI. |
| `failed`        | `int`   | Elements that could not be healed. |
| `success_rate`  | `float` | Percentage of passed + healed. |
| `results`       | `list[ElementAuditResult]` | Detailed result for each element. |
| `start_time`    | `datetime` | When the audit started. |
| `end_time`      | `datetime` | When the audit ended. |
| `to_dict()`     | `dict`  | Serialize to a dictionary. |

### Using the Auditor Directly

```python
import asyncio
from core.config_manager import ConfigManager
from core.auditor import Auditor

async def custom_audit():
    config = ConfigManager("config.json")
    auditor = Auditor(config)

    # Set progress callbacks
    auditor.set_callbacks(
        on_element_audited=lambda result: print(f"{result.status.value}: {result.element_name}"),
        on_page_started=lambda name, url: print(f"Page: {name}"),
    )

    report = await auditor.run_audit("input/scripts/01_herokuapp_login.json")
    return report

report = asyncio.run(custom_audit())
```

---

## 6. Input Script Specification

### JSON Schema

```json
{
  "name": "<string, required>",
  "base_url": "<string, required>",
  "metadata": {
    "author": "<string, optional>",
    "version": "<string, optional>",
    "description": "<string, optional>",
    "created": "<string, optional>"
  },
  "pages": [
    {
      "name": "<string, required>",
      "url": "<string, required>",
      "description": "<string, optional>",
      "elements": [
        {
          "name": "<string, required>",
          "strategy": "<string, required>",
          "value": "<string, required>",
          "intent": "<string, optional but recommended>",
          "line_number": "<integer, optional>",
          "file_path": "<string, optional>"
        }
      ]
    }
  ]
}
```

### URL Resolution

- If `page.url` starts with `http://` or `https://`, it is used as-is (absolute URL).
- Otherwise, it is appended to `base_url`:
  - `base_url`: `"https://example.com"` + `url`: `"/login"` = `"https://example.com/login"`

### Strategy Values

| Value               | Playwright Selector Translation | Example Value |
|---------------------|---------------------------------|---------------|
| `id`                | `#value`                        | `username` |
| `css`               | `value` (as-is)                 | `button.submit` |
| `xpath`             | `xpath=value`                   | `//div[@class='header']` |
| `name`              | `[name='value']`                | `email` |
| `class_name`        | `.value`                        | `btn-primary` |
| `tag_name`          | `value` (as-is)                 | `h1` |
| `link_text`         | `text=value`                    | `Sign In` |
| `partial_link_text` | `text=value`                    | `Sign` |

---

## 7. AI Provider Details

### Prompt Structure

All providers receive the same standardized prompt (defined in `BaseAIProvider._build_healing_prompt()`):

```
You are an expert test automation engineer...

## Failed Locator
{broken_locator}

## Page URL
{page_url}

## Element Intent
{intent}

## Surrounding HTML
{html_snippet}

## Computed CSS Properties
{css_properties}

## Instructions
Generate exactly 3 locator candidates...
```

### Expected AI Response Format

```json
[
  {
    "strategy": "id",
    "value": "username",
    "reasoning": "The input has a stable id attribute",
    "confidence": 0.95
  },
  {
    "strategy": "css",
    "value": "input[name='username']",
    "reasoning": "Name attribute is also stable",
    "confidence": 0.90
  },
  {
    "strategy": "xpath",
    "value": "//input[@id='username']",
    "reasoning": "XPath using the id attribute",
    "confidence": 0.85
  }
]
```

### Provider-Specific Configuration

| Provider | Model Parameter      | Vision Support | Temperature | Max Tokens |
|----------|----------------------|----------------|-------------|------------|
| Gemini   | `gemini-2.5-pro`     | Yes (inline bytes) | 0.2      | 2048       |
| OpenAI   | `gpt-4o`             | Yes (base64 URL)   | 0.2      | 2048       |
| Claude   | `claude-3-5-sonnet-20241022` | Yes (base64 source) | 0.2 | 2048       |

### Response Parsing

All providers use the same fallback parsing strategy:

1. Try to parse the response as raw JSON.
2. If it starts with triple backticks (code fence), strip them and parse.
3. If that fails, search for the first `[` and last `]` in the text and parse the substring.
4. If all parsing fails, return an empty list.

---

## 8. Forensic Evidence Specification

When a locator fails, `ForensicAgent.collect_evidence()` captures:

### Files Saved

| File Pattern                           | Type       | Description |
|----------------------------------------|------------|-------------|
| `{name}_{timestamp}_full_page.png`     | PNG Image  | Full-page screenshot (scrolled). |
| `{name}_{timestamp}_target_area.png`   | PNG Image  | Element screenshot if the element was partially found, otherwise a viewport screenshot. |
| `{name}_{timestamp}_DOM_structure.html`| HTML File  | Complete page HTML source. |

### ForensicEvidence Object Fields

| Field                    | Type   | Description |
|--------------------------|--------|-------------|
| `full_page_screenshot`   | string | File path to the full-page screenshot. |
| `target_area_screenshot` | string | File path to the target-area screenshot. |
| `dom_snapshot_path`      | string | File path to the saved HTML. |
| `html_snippet`           | string | HTML fragment of the parent element or first 5000 chars of body. |
| `css_properties`         | dict   | Computed CSS of up to 10 interactive elements on the page. |
| `page_url`               | string | Current page URL. |
| `page_title`             | string | Current page title. |
| `viewport_size`          | dict   | `{"width": 1920, "height": 1080}` |
| `timestamp`              | datetime | When the evidence was captured. |

### CSS Properties Captured

For each candidate element, these computed styles are captured:

`display`, `visibility`, `opacity`, `text`, `tag`, `id`, `classes`, `type`, `role`

---

## 9. Self-Healing Engine Internals

### `HealingEngine.heal_element()` Flow

```
Input: PageElement, page_url
Output: ElementAuditResult

FOR attempt = 1 to retry_limit:
    │
    ├── provider = ProviderFactory.get_provider()
    ├── evidence = ForensicAgent.collect_evidence(locator, page_name)
    │
    ├── ai_suggestions = provider.generate_locators(
    │       broken_locator, html_snippet, css_properties, intent, page_url, screenshot
    │   )
    │
    ├── candidate_list = LocatorValidator.build_candidate_list(
    │       broken_locator, ai_suggestions, provider_name
    │   )
    │
    ├── selected = LocatorValidator.validate_candidates(candidate_list, page_url)
    │
    ├── IF selected:
    │       result.status = HEALED
    │       result.healed_locator = selected
    │       RETURN result
    │
    └── ELSE:
            CONTINUE to next attempt

result.status = FAILED
RETURN result
```

### Candidate Validation Process

For each AI-generated candidate `(strategy, value)`:

1. **Duplicate Check:** Query `KnownLocatorsDB.is_duplicate(strategy, value)`. If the locator belongs to a different element, **skip**.
2. **Live Test:** Call `BrowserEngine.find_element_raw(strategy, value)`. If `None`, mark as **invalid**.
3. **Visibility Score:** Call `BrowserEngine.get_element_visibility_score(element)`:
   - `+0.4` if element is visible.
   - `+0.3` if element is within the viewport.
   - `+0.2` if element has non-zero dimensions.
   - `+0.1` if element is enabled (interactive).
   - Total score range: `0.0` to `1.0`.
4. **Threshold:** Score must be `>= 0.3` to be considered valid.
5. **Selection:** Among all validated candidates, the one with the **highest visibility score** wins.

---

## 10. Locator Validation & Scoring

### Visibility Score Breakdown

| Component          | Points | Condition |
|--------------------|--------|-----------|
| Visible            | 0.4    | `element.is_visible() == True` |
| In Viewport        | 0.3    | Bounding box fully within viewport dimensions |
| Has Size           | 0.2    | `width * height > 0` |
| Enabled            | 0.1    | `element.is_enabled() == True` |
| **Maximum Score**  | **1.0**| All conditions met |

### Minimum Threshold

An element must score **>= 0.3** to pass validation. This means at minimum:
- It must be **visible** (0.4 alone passes), OR
- It must be in-viewport with non-zero size (0.3 + 0.2 = 0.5).

### Strategy Parsing

The `LocatorValidator._parse_strategy()` method normalizes AI response strategy strings:

| AI Returns              | Maps To              |
|-------------------------|----------------------|
| `xpath`                 | `LocatorStrategy.XPATH` |
| `css`, `css_selector`, `css-selector` | `LocatorStrategy.CSS` |
| `id`                    | `LocatorStrategy.ID` |
| `name`                  | `LocatorStrategy.NAME` |
| `class_name`, `class`   | `LocatorStrategy.CLASS_NAME` |
| `tag_name`, `tag`       | `LocatorStrategy.TAG_NAME` |
| `link_text`             | `LocatorStrategy.LINK_TEXT` |
| Any other               | `LocatorStrategy.CSS` (fallback) |

---

## 11. File Modification Rules

### How `FileModifier` Updates Source Files

1. Read the entire file into memory.
2. Search for any line containing the exact old locator value string.
3. Replace the old value with the new value on that line.
4. Insert a documentation comment on the line immediately above:
   ```
   {indent}# AI-Generated on {YYYY-MM-DD}: verified via {provider} - {reasoning}
   ```
5. Write the modified content back to the file.

### Comment Style by File Extension

| Extension     | Comment Prefix |
|---------------|----------------|
| `.py`, `.rb`  | `#`            |
| `.java`, `.js`, `.ts`, `.cs` | `//` |
| All others    | `//` (default) |

### Fallback: Regex Replacement

If the exact string match fails, the modifier attempts regex-based replacement using `re.escape(old_value)`.

### Prerequisites for File Modification

For a file to be modified, the element definition must include both:
- `file_path`: The path to the source file.
- The old locator value must exist as a substring in at least one line of the file.

If `file_path` is not set, healing still works (locator is validated), but no file is modified and no commit is made.

---

## 12. Git Integration Specification

### Commit Message Format

```
[AI-HEAL] Updated locator for object: {object_name} on page: {page_url}

Provider: {ai_provider}
Auto-healed by Loctor Builder
```

### GitManager Behavior

| Scenario                      | Action |
|-------------------------------|--------|
| `auto_commit = true`, `--repo` provided | Stage file and commit. |
| `auto_commit = true`, no `--repo`       | Skip (no repo initialized). |
| `auto_commit = false`                    | Skip (disabled in config). |
| Git repo not found at `--repo` path     | Initialize a new repo, then commit. |

### Staged Files

Only the specific source file that was modified is staged. No other files are included in the commit.

---

## 13. Web Dashboard API Reference

The dashboard exposes the following HTTP endpoints:

### `GET /`

Returns the HTML dashboard page.

### `GET /api/config`

Returns the current configuration (API keys are redacted).

**Response:**

```json
{
  "active_provider": "gemini",
  "providers": {
    "gemini": { "model": "gemini-2.5-pro", "api_key": "***REDACTED***" }
  },
  "settings": { ... }
}
```

### `POST /api/provider`

Switch the active AI provider.

**Request Body:**

```json
{ "provider": "openai" }
```

**Response:**

```json
{ "success": true, "provider": "openai" }
```

### `POST /api/settings`

Update a single setting.

**Request Body:**

```json
{ "key": "retry_limit", "value": 5 }
```

**Response:**

```json
{ "success": true, "key": "retry_limit", "value": 5 }
```

### `GET /api/stats`

Returns system status.

### WebSocket Events (SocketIO)

| Event             | Direction       | Payload |
|-------------------|-----------------|---------|
| `config_updated`  | Server -> Client | `{ "provider": "openai" }` or `{ "key": "value" }` |
| `element_audited` | Server -> Client | `{ "element_name": "...", "page_name": "...", "status": "passed" }` |
| `page_started`    | Server -> Client | `{ "page_name": "...", "url": "..." }` |

---

## 14. Data Models Reference

### `LocatorStrategy` (Enum)

```
XPATH, CSS, ID, NAME, CLASS_NAME, TAG_NAME, LINK_TEXT, PARTIAL_LINK_TEXT
```

### `LocatorStatus` (Enum)

```
VALID, BROKEN, HEALED, UNVERIFIED
```

### `AuditStatus` (Enum)

```
PASSED, FAILED, HEALED, SKIPPED
```

### `Locator` (Dataclass)

| Field           | Type              | Description |
|-----------------|-------------------|-------------|
| `strategy`      | `LocatorStrategy` | The locator strategy type. |
| `value`         | `str`             | The locator expression. |
| `object_name`   | `str`             | Name of the element this locator identifies. |
| `description`   | `str`             | Human-readable description. |
| `status`        | `LocatorStatus`   | Current validation status. |
| `confidence`    | `float`           | AI confidence score (0.0 - 1.0). |
| `last_verified` | `Optional[datetime]` | When the locator was last verified. |

### `LocatorCandidate` (Dataclass)

| Field              | Type      | Description |
|--------------------|-----------|-------------|
| `locator`          | `Locator` | The candidate locator. |
| `rank`             | `int`     | Rank order from AI (1 = first suggestion). |
| `ai_provider`      | `str`     | Which AI provider generated this. |
| `reasoning`        | `str`     | AI's explanation for this locator. |
| `visibility_score` | `float`   | Computed visibility score after live testing. |
| `validated`        | `bool`    | Whether the candidate passed live validation. |

### `ElementAuditResult` (Dataclass)

| Field              | Type                        | Description |
|--------------------|-----------------------------|-------------|
| `element_name`     | `str`                       | Name of the element. |
| `page_name`        | `str`                       | Name of the page. |
| `original_locator` | `Locator`                   | The original locator that was tested. |
| `status`           | `AuditStatus`               | Final status after audit. |
| `healed_locator`   | `Optional[LocatorCandidate]`| The selected healed locator (if healed). |
| `forensic_evidence`| `Optional[ForensicEvidence]`| Captured evidence (if element failed). |
| `error_message`    | `str`                       | Error details (if failed). |
| `healing_attempts` | `int`                       | Number of AI healing attempts made. |

---

## 15. Output & Reporting Specification

### Output Directory Structure

```
logs/
├── screenshots/
│   ├── Login_Page_username_input_20260216_143022_full_page.png
│   ├── Login_Page_username_input_20260216_143022_target_area.png
│   └── ...
├── dom/
│   ├── Login_Page_username_input_20260216_143022_DOM_structure.html
│   └── ...
├── reports/
│   ├── audit_HerokuApp Login Flow_20260216_143022.json
│   ├── test_run_20260216_143100.json
│   └── ...
├── loctor_builder.log
└── test_runner.log

data/
└── known_locators.json
```

### Audit Report JSON Structure

See [Section 8 of the User Guide](USER_GUIDE.md#8-reading-audit-results) for the complete JSON structure.

### Test Runner Report JSON Structure

```json
{
  "run_time": "2026-02-16T14:31:00",
  "total_duration": 45.2,
  "test_filter": "all",
  "results": [
    {
      "test_name": "Quick Validation (All Valid Locators)",
      "script": "input/scripts/01_herokuapp_login.json",
      "total": 5,
      "passed": 5,
      "healed": 0,
      "failed": 0,
      "success_rate": 100.0,
      "duration_seconds": 8.3,
      "provider": "gemini",
      "status": "COMPLETED"
    }
  ]
}
```

---

## 16. Logging Configuration

### Log Levels

| Level   | What It Captures |
|---------|------------------|
| `DEBUG` | Element lookup attempts, AI response parsing, selector translation, every step. |
| `INFO`  | Navigation events, element pass/fail, healing results, file updates, commits. |
| `WARNING` | Low visibility scores, failed parsing, missing file paths. |
| `ERROR` | API failures, browser crashes, file I/O errors, Git failures. |

### Log Output Destinations

| Destination                   | Format |
|-------------------------------|--------|
| Console (stdout)              | `HH:MM:SS [LEVEL] module: message` |
| `logs/loctor_builder.log`     | `YYYY-MM-DD HH:MM:SS [LEVEL] module: message` |
| `logs/test_runner.log`        | Same as above (when using test_runner.py) |

### Changing the Log Level

In `config.json`:

```json
"log_level": "DEBUG"
```

---

## 17. Error Handling & Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Config file not found: config.json` | Missing config file. | Ensure `config.json` exists in the working directory. |
| `API key not configured for provider 'gemini'` | Key is still `YOUR_KEY_HERE`. | Set the key in `.env` or `config.json`. |
| `Script file not found: ...` | Wrong path to input script. | Check the file path. Use relative paths from the project root. |
| `Navigation failed: Timeout` | Target website is slow or unreachable. | Increase `validation_timeout` in config. Check your internet connection. |
| `Gemini API error: 429 Too Many Requests` | AI rate limit hit. | Wait and retry, or switch to a different provider. |
| `No valid candidate found` | AI suggestions didn't match any element. | Improve the `intent` field. Try a different provider. Increase `retry_limit`. |
| `playwright._impl._errors.Error: Executable doesn't exist` | Browser not installed. | Run `playwright install chromium`. |

### Debug Mode

For maximum diagnostic output:

1. Set `log_level` to `DEBUG` in `config.json`.
2. Run with `--no-headless` to see the browser.
3. Check `logs/loctor_builder.log` for full details.

---

## 18. Security Considerations

### API Key Protection

| Mechanism      | Description |
|----------------|-------------|
| `.env` file    | Keys are stored in `.env`, which is listed in `.gitignore`. |
| `.gitignore`   | `.env`, `*.env`, and `config_local.json` are excluded from Git. |
| `to_dict()`    | The `ConfigManager.to_dict()` method always redacts API keys as `***REDACTED***`. |
| Dashboard API  | The `/api/config` endpoint uses `to_dict()`, so keys are never exposed in the UI. |

### Recommendations

1. **Never commit `.env`** to version control.
2. **Use environment variables** in CI/CD instead of `config.json`.
3. **Rotate keys** if you suspect they've been exposed.
4. **Use read-only Git tokens** if enabling auto-commit in shared environments.

---

## 19. Performance Tuning

### Timeout Optimization

| Setting               | Low Latency  | High Reliability |
|-----------------------|--------------|------------------|
| `validation_timeout`  | `3000`       | `10000`          |
| `retry_limit`         | `1`          | `5`              |

### Browser Performance

| Setting       | Faster         | More Compatible |
|---------------|----------------|-----------------|
| `headless`    | `true`         | `true`          |
| `browser`     | `chromium`     | `chromium`      |
| `viewport_*`  | `1280x720`    | `1920x1080`     |

### Network Considerations

- Each AI healing attempt involves one API call (text + optional image).
- Screenshots are encoded as base64 and sent to the AI. Full-page screenshots can be large.
- For faster healing, ensure your AI provider has low latency in your region.

---

## 20. Extending the System

### Adding a New AI Provider

1. Create `ai/my_provider.py`:

```python
from ai.base_provider import BaseAIProvider

class MyProvider(BaseAIProvider):
    def __init__(self, model: str, api_key: str):
        super().__init__(model, api_key)
        self._name = "MyProvider"

    async def generate_locators(self, broken_locator, html_snippet,
                                 css_properties, intent, page_url,
                                 screenshot_path=None):
        prompt = self._build_healing_prompt(
            broken_locator, html_snippet, css_properties, intent, page_url
        )
        # Call your API here
        # Return list of dicts: [{"strategy": "...", "value": "...", "reasoning": "...", "confidence": 0.9}]
        ...

    async def analyze_element(self, html_snippet, css_properties,
                               screenshot_path=None):
        # Return a dict describing the element
        ...
```

2. Register it in `ai/provider_factory.py`:

```python
from ai.my_provider import MyProvider

_PROVIDERS = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "my_provider": MyProvider,     # <-- add this
}
```

3. Add config in `config.json`:

```json
"my_provider": {
  "model": "my-model-name",
  "api_key": "YOUR_KEY_HERE"
}
```

### Adding a New Locator Strategy

1. Add the strategy to `models/locator.py`:

```python
class LocatorStrategy(enum.Enum):
    ...
    DATA_TESTID = "data_testid"
```

2. Add the Playwright selector mapping in `core/browser_engine.py`:

```python
elif strategy == "data_testid":
    return f"[data-testid='{value}']"
```

3. Add the parser mapping in `core/locator_validator.py` and `core/script_loader.py`.

---

*End of User Manual*
