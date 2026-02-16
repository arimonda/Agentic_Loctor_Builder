# Loctor Builder - Architecture Document

> **AI-Powered Autonomous Locator Validator & Self-Healing Engine**
>
> Version: 1.0 | Last Updated: 2026-02-16

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Directory Structure](#3-directory-structure)
4. [High-Level Architecture](#4-high-level-architecture)
5. [Component Deep Dive](#5-component-deep-dive)
   - 5.1 [Entry Points](#51-entry-points)
   - 5.2 [Core Engine](#52-core-engine)
   - 5.3 [AI Provider Layer](#53-ai-provider-layer)
   - 5.4 [Data Models](#54-data-models)
   - 5.5 [Web Dashboard (UI)](#55-web-dashboard-ui)
   - 5.6 [Input Layer](#56-input-layer)
6. [Data Flow & Sequence Diagrams](#6-data-flow--sequence-diagrams)
   - 6.1 [End-to-End Audit Flow](#61-end-to-end-audit-flow)
   - 6.2 [Self-Healing Pipeline](#62-self-healing-pipeline)
   - 6.3 [Candidate Validation Flow](#63-candidate-validation-flow)
7. [Design Patterns](#7-design-patterns)
8. [Configuration System](#8-configuration-system)
9. [AI Provider Architecture](#9-ai-provider-architecture)
10. [Browser Automation Layer](#10-browser-automation-layer)
11. [Persistence & Storage](#11-persistence--storage)
12. [Error Handling Strategy](#12-error-handling-strategy)
13. [Logging & Reporting](#13-logging--reporting)
14. [External Dependencies](#14-external-dependencies)
15. [Security Considerations](#15-security-considerations)
16. [Extensibility Guide](#16-extensibility-guide)

---

## 1. Executive Summary

**Loctor Builder** is an autonomous, AI-powered locator validator and self-healing engine for web automation test suites. When a UI locator (CSS selector, XPath, ID, etc.) breaks due to front-end changes, the system:

1. **Detects** the failure by testing locators against a live web page.
2. **Collects forensic evidence** — screenshots, DOM snapshots, surrounding HTML/CSS.
3. **Consults an AI model** (Google Gemini, OpenAI GPT-4o, or Anthropic Claude) to generate replacement locator candidates.
4. **Validates** each candidate on the live page and checks for duplicates.
5. **Updates** the source code with the healed locator plus an audit comment.
6. **Auto-commits** the change to Git with a standardized `[AI-HEAL]` commit message.

The system supports three AI providers, a real-time web dashboard, a rich CLI, and a comprehensive reporting layer.

---

## 2. System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LOCTOR BUILDER                                     │
│                                                                                 │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────────────────────────────────┐ │
│  │          │   │              │   │            CORE ENGINE                   │ │
│  │   CLI    │──▶│   Auditor    │──▶│  Browser ─▶ Forensic ─▶ Healing ─▶ Git  │ │
│  │  (Click) │   │ (Orchestrator│   │  Engine     Agent       Engine     Mgr   │ │
│  │          │   │              │   │                                          │ │
│  ├──────────┤   │              │   │  ScriptLoader ◀── JSON Script Files      │ │
│  │   Web    │──▶│              │──▶│  FileModifier ──▶ Source Code Updates     │ │
│  │Dashboard │   │              │   │  KnownLocatorsDB ──▶ Duplicate Prevention│ │
│  │ (Flask)  │   └──────────────┘   └──────────────────────────────────────────┘ │
│  └──────────┘          │                                                        │
│                        ▼                                                        │
│           ┌──────────────────────┐    ┌────────────────────────────────────┐    │
│           │   AI PROVIDER LAYER  │    │          DATA MODELS               │    │
│           │                      │    │                                    │    │
│           │  ┌────────────────┐  │    │  Locator / LocatorCandidate       │    │
│           │  │ BaseAIProvider │  │    │  PageElement / PageObject          │    │
│           │  └───────┬────────┘  │    │  AutomationScript                 │    │
│           │    ┌─────┼─────┐     │    │  AuditReport / ForensicEvidence   │    │
│           │    ▼     ▼     ▼     │    │  ElementAuditResult               │    │
│           │ Gemini OpenAI Claude │    └────────────────────────────────────┘    │
│           │ (2.5Pro)(GPT4o)(3.5) │                                              │
│           └──────────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Directory Structure

```
Agentic_Loctor_Builder/
│
├── main.py                                # Application entry point
├── cli.py                                 # Click-based CLI interface
├── test_runner.py                         # End-to-end test suite runner
├── config.json                            # Central configuration file
├── .env                                   # Environment variables (secrets)
├── .env.example                           # Environment template
├── .gitignore                             # Git ignore rules
├── requirements.txt                       # Python dependencies (19 packages)
├── README.md                              # Project overview
├── USER_MANUAL.md                         # Technical reference manual
├── USER_GUIDE.md                          # User-facing guide
├── ARCHITECTURE.md                        # This document
│
├── ai/                                    # AI Provider Layer
│   ├── base_provider.py                   #   Abstract base class (ABC)
│   ├── gemini_provider.py                 #   Google Gemini implementation
│   ├── openai_provider.py                 #   OpenAI GPT-4o implementation
│   ├── claude_provider.py                 #   Anthropic Claude implementation
│   └── provider_factory.py               #   Factory + instance caching
│
├── core/                                  # Core Engine
│   ├── auditor.py                         #   Main workflow orchestrator
│   ├── config_manager.py                  #   Singleton config (thread-safe)
│   ├── browser_engine.py                  #   Playwright browser wrapper
│   ├── forensic_agent.py                  #   Screenshot/DOM/CSS capture
│   ├── healing_engine.py                  #   Self-healing coordinator
│   ├── locator_validator.py               #   Live candidate validation
│   ├── known_locators_db.py               #   TinyDB duplicate prevention
│   ├── file_modifier.py                   #   Source code updater
│   ├── git_manager.py                     #   Git auto-commit manager
│   └── script_loader.py                   #   JSON script parser
│
├── models/                                # Data Models (dataclasses)
│   ├── locator.py                         #   Locator, LocatorCandidate, enums
│   ├── page_object.py                     #   PageElement, PageObject, Script
│   └── audit_result.py                    #   AuditReport, ForensicEvidence
│
├── ui/                                    # Web Dashboard
│   └── dashboard.py                       #   Flask + SocketIO (dark theme)
│
├── input/                                 # Input Files
│   ├── scripts/                           #   JSON automation script definitions
│   │   ├── 01_herokuapp_login.json        #     Valid locators test
│   │   ├── 02_herokuapp_broken_locators.json  #  Broken locators (healing demo)
│   │   ├── 03_herokuapp_multi_page.json   #     Multi-page navigation test
│   │   └── 04_herokuapp_mixed_strategies.json # Mixed strategy test
│   ├── page_objects/                      #   Sample Page Object source files
│   │   ├── login_page.py                  #     Login page (all valid)
│   │   ├── login_page_broken.py           #     Login page (broken locators)
│   │   ├── checkboxes_page.py             #     Checkboxes page
│   │   ├── dropdown_page.py               #     Dropdown page
│   │   ├── form_auth_page.py              #     Form auth page
│   │   └── mixed_strategies.py            #     Mixed locator types
│   └── test_configs/                      #   Preset configurations
│
├── logs/                                  # Runtime Output (git-ignored)
│   ├── screenshots/                       #   Forensic screenshots (.png)
│   ├── dom/                               #   DOM snapshots (.html)
│   ├── reports/                           #   Audit reports (.json)
│   ├── loctor_builder.log                 #   Application log
│   └── test_runner.log                    #   Test runner log
│
└── data/                                  # Persistent Data (git-ignored)
    └── known_locators.json                #   TinyDB database
```

---

## 4. High-Level Architecture

The system follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                  │
│         CLI (Click + Rich)  |  Web Dashboard (Flask) │
├─────────────────────────────────────────────────────┤
│                 ORCHESTRATION LAYER                   │
│                     Auditor                           │
│          (coordinates all core components)            │
├─────────────────────────────────────────────────────┤
│                   CORE SERVICES                      │
│  BrowserEngine | ForensicAgent | HealingEngine       │
│  LocatorValidator | FileModifier | GitManager         │
│  ScriptLoader | KnownLocatorsDB                      │
├─────────────────────────────────────────────────────┤
│                 AI PROVIDER LAYER                     │
│    BaseAIProvider → Gemini | OpenAI | Claude          │
│                  ProviderFactory                      │
├─────────────────────────────────────────────────────┤
│                   DATA MODEL LAYER                   │
│  Locator | LocatorCandidate | PageElement | Report    │
├─────────────────────────────────────────────────────┤
│                 INFRASTRUCTURE LAYER                  │
│  Playwright | TinyDB | GitPython | python-dotenv      │
└─────────────────────────────────────────────────────┘
```

---

## 5. Component Deep Dive

### 5.1 Entry Points

#### `main.py` — Application Entry Point

| Aspect       | Detail                                                   |
|--------------|----------------------------------------------------------|
| **Purpose**  | Bootstraps logging, delegates to CLI or programmatic API |
| **Functions**| `setup_logging()`, `run_audit()`, `main()`               |
| **Pattern**  | Facade — hides internal wiring from the caller           |

**Programmatic API:**
```python
from main import run_audit
import asyncio

report = asyncio.run(run_audit("scripts/my_script.json", provider="gemini"))
```

**CLI delegation:**
```python
def main():
    from cli import cli
    setup_logging()
    cli()
```

#### `cli.py` — Command-Line Interface

| Aspect       | Detail                                              |
|--------------|-----------------------------------------------------|
| **Framework**| Click (command groups) + Rich (colored output)       |
| **Commands** | `audit`, `switch`, `status`, `providers`, `dashboard`|

| Command      | Description                                    | Key Options                        |
|--------------|------------------------------------------------|------------------------------------|
| `audit`      | Run locator audit on a script                  | `--repo`, `--provider`, `--headless` |
| `switch`     | Change active AI provider at runtime           | Accepts `gemini`, `openai`, `claude` |
| `status`     | Display current configuration as Rich table    | —                                  |
| `providers`  | List all providers with API key status         | —                                  |
| `dashboard`  | Launch the Flask web dashboard                 | Respects `dashboard_port` setting  |

**Progress Callbacks:** The CLI registers `on_element_audited` and `on_page_started` callbacks on the `Auditor` to print color-coded, real-time results:
- Green: `PASSED`
- Yellow: `HEALED`
- Red: `FAILED`
- Dim: `SKIPPED`

#### `test_runner.py` — End-to-End Test Suite

| Test Name                  | Script                                  | Purpose                           |
|----------------------------|-----------------------------------------|-----------------------------------|
| Quick Validation           | `01_herokuapp_login.json`               | All valid locators (smoke test)   |
| Self-Healing               | `02_herokuapp_broken_locators.json`     | Broken locators trigger AI healing|
| Multi-Page Navigation      | `03_herokuapp_multi_page.json`          | Cross-page navigation audit       |
| Mixed Locator Strategies   | `04_herokuapp_mixed_strategies.json`    | ID, CSS, XPath, Name on one page  |

Output: JSON reports saved to `logs/reports/test_run_<timestamp>.json`.

---

### 5.2 Core Engine

#### `core/auditor.py` — Auditor (Main Orchestrator)

The `Auditor` is the **central coordinator** that drives the entire audit workflow. It wires together all other components.

```
                           Auditor
                              │
            ┌─────────┬───────┼──────────┬──────────┐
            ▼         ▼       ▼          ▼          ▼
      BrowserEngine  Forensic  Healing  FileModifier GitManager
                     Agent     Engine
                                 │
                        ┌────────┼────────┐
                        ▼        ▼        ▼
                   ProviderFactory  Validator  KnownDB
```

**Class: `Auditor`**

| Method                  | Purpose                                                 |
|-------------------------|---------------------------------------------------------|
| `__init__(config)`      | Initializes all sub-components                          |
| `set_callbacks()`       | Registers progress callback functions                   |
| `run_audit(script, repo)` | Main async entry — loads script, loops pages/elements |
| `_audit_element(elem, url)` | Verifies one element; triggers healing if broken    |
| `_apply_heal(elem, result, url)` | Updates source file + commits via Git          |
| `_resolve_url(base, page)` | Resolves relative page URLs against base URL         |
| `_save_report(name)`   | Serializes `AuditReport` to JSON in `logs/reports/`     |

**Lifecycle:**
1. Load script via `ScriptLoader`
2. Start browser via `BrowserEngine`
3. For each page: navigate, then audit each element
4. For each element: verify → heal if broken → update file → commit
5. Stop browser, save report

#### `core/browser_engine.py` — BrowserEngine

Wraps **Playwright** (async API) to provide locator-agnostic element finding.

**Class: `BrowserEngine`**

| Method                              | Purpose                                             |
|-------------------------------------|-----------------------------------------------------|
| `start()`                           | Launch browser (Chromium/Firefox/WebKit)            |
| `stop()`                            | Gracefully close browser context                    |
| `navigate(url, wait_until)`         | Navigate with configurable wait strategy            |
| `find_element(locator)`             | Find element using typed `Locator` object           |
| `find_element_raw(strategy, value)` | Find element using raw strings (for candidate testing)|
| `get_element_visibility_score(el)`  | Calculate 0.0–1.0 visibility score                  |
| `get_element_html(locator)`         | Get parent HTML or fallback to first 5000 chars of body|
| `get_element_css(element)`          | Extract 16 computed CSS properties                  |
| `get_surrounding_elements_css(loc)` | Get CSS of up to 10 nearby interactive elements     |
| `take_screenshot(path, full_page)`  | Full-page or viewport screenshot                    |
| `take_element_screenshot(el, path)` | Cropped element screenshot                          |

**Selector Translation:**
The engine translates the application's `LocatorStrategy` enum into Playwright selectors:

| Strategy         | Playwright Selector     |
|------------------|-------------------------|
| `xpath`          | `xpath=<value>`         |
| `css`            | `<value>` (native CSS)  |
| `id`             | `#<value>`              |
| `name`           | `[name='<value>']`      |
| `class_name`     | `.<value>`              |
| `tag_name`       | `<value>`               |
| `link_text`      | `text=<value>`          |
| `partial_link_text` | `text=<value>`       |

**Visibility Scoring Algorithm:**
```
Score = 0.0
  + 0.4  if element is visible (not hidden by CSS)
  + 0.3  if element is within the viewport bounds
  + 0.2  if element has non-zero area (width × height > 0)
  + 0.1  if element is enabled (not disabled)
────────
Max: 1.0

Minimum threshold for PASSED/HEALED: 0.3
```

#### `core/forensic_agent.py` — ForensicAgent

Captures comprehensive forensic evidence when a locator fails — providing the AI with rich context for generating replacements.

**Class: `ForensicAgent`**

| Method                      | Output                                        |
|-----------------------------|-----------------------------------------------|
| `collect_evidence(loc, page)` | Returns `ForensicEvidence` dataclass         |
| `_capture_full_page_screenshot()` | `logs/screenshots/<name>_<ts>_full_page.png` |
| `_capture_target_area_screenshot()` | Element screenshot or viewport fallback    |
| `_capture_dom()`            | `logs/dom/<name>_<ts>_DOM_structure.html`     |

**Evidence Package:**
```
ForensicEvidence
├── full_page_screenshot    → PNG file path
├── target_area_screenshot  → PNG file path (element or viewport)
├── dom_snapshot_path       → HTML file path
├── html_snippet            → String (parent element HTML or first 5KB of body)
├── css_properties          → Dict of nearby elements' CSS
├── page_url                → Current page URL
├── page_title              → Current page title
├── viewport_size           → {width, height}
└── timestamp               → datetime
```

#### `core/healing_engine.py` — HealingEngine

Coordinates the AI consultation and validation loop.

**Class: `HealingEngine`**

| Method                       | Purpose                                       |
|------------------------------|-----------------------------------------------|
| `heal_element(element, url)` | Full healing pipeline with retry logic        |

**Algorithm:**
```
FOR attempt = 1 TO retry_limit (default: 3):
    1. Collect forensic evidence (ForensicAgent)
    2. Call AI provider: generate_locators(broken, html, css, intent, url, screenshot)
    3. Build LocatorCandidateList from AI suggestions
    4. Validate candidates on live page (LocatorValidator)
    5. IF validated candidate found:
         → Return HEALED result
    6. ELSE:
         → Log warning, retry
END FOR
→ Return FAILED result
```

#### `core/locator_validator.py` — LocatorValidator

Tests AI-generated candidates against the live page and prevents duplicate assignments.

**Class: `LocatorValidator`**

| Method                          | Purpose                                        |
|---------------------------------|------------------------------------------------|
| `validate_candidates(list, url)` | Test each candidate; select best             |
| `build_candidate_list(broken, suggestions, provider)` | Convert AI output → typed models |
| `_parse_strategy(str)`          | Normalize strategy strings to enum             |

**Validation Pipeline per Candidate:**
```
1. Check KnownLocatorsDB for duplicate
   └── IF same locator assigned to different element → SKIP

2. Test on live page: BrowserEngine.find_element_raw(strategy, value)
   └── IF not found → MARK as not validated

3. Calculate visibility score
   └── IF score < 0.3 → MARK as not validated

4. IF score >= 0.3 → MARK as validated, set status = HEALED
```

**Best Candidate Selection:**
- Filter: Only validated candidates
- Sort: By `visibility_score` descending
- Select: First (highest score)
- Side effect: Add selected locator to `KnownLocatorsDB`

#### `core/known_locators_db.py` — KnownLocatorsDB

Prevents the same locator from being assigned to multiple different elements — a critical integrity check.

**Class: `KnownLocatorsDB`**

| Method                            | Purpose                                 |
|-----------------------------------|-----------------------------------------|
| `add_locator(strategy, value, ...)` | Insert locator record                 |
| `find_duplicate(strategy, value)` | Check if locator exists                 |
| `is_duplicate(strategy, value)`   | Boolean check                           |
| `get_locators_for_object(name)`   | Get all locators for a named element    |
| `remove_locator(strategy, value)` | Delete a record                         |
| `clear()`                         | Truncate entire database                |

**Storage:** TinyDB JSON file at `./data/known_locators.json`

**Schema:**
```json
{
    "strategy": "id",
    "value": "username",
    "object_name": "username_input",
    "page_url": "https://the-internet.herokuapp.com/login",
    "source": "ai-healed-gemini"
}
```

#### `core/file_modifier.py` — FileModifier

Updates source code files with the healed locator value and adds an AI-generated documentation comment.

**Class: `FileModifier`**

| Method                              | Purpose                                    |
|-------------------------------------|--------------------------------------------|
| `update_locator_in_file(path, old, new, provider)` | Main update method            |
| `find_locator_line(path, value)`    | Find line number of a locator value        |
| `_try_regex_replacement()`          | Fallback regex-based replacement           |
| `_build_comment(path, provider, reasoning)` | Generate comment for the healed line|
| `_get_indent(line)`                 | Preserve original indentation              |

**Comment Format by Language:**
| Extension     | Comment Style                                                                  |
|---------------|--------------------------------------------------------------------------------|
| `.py`, `.rb`  | `# AI-Generated on 2026-02-16: verified via Gemini - <reasoning>`             |
| `.java`, `.js`, `.ts`, `.cs` | `// AI-Generated on 2026-02-16: verified via Gemini - <reasoning>` |

**Before/After Example:**
```python
# Before:
    USERNAME_INPUT = (By.ID, "txt_username_BROKEN")

# After:
    # AI-Generated on 2026-02-16: verified via Gemini - Stable ID attribute matches the input field
    USERNAME_INPUT = (By.ID, "username")
```

**Supported Frameworks:**
- Python Selenium (`find_element(By.XXX, "...")`)
- Java Selenium (`findElement(By.xxx("..."))`)
- JavaScript/Playwright (`page.locator("...")`)
- Generic string matching (fallback)

#### `core/git_manager.py` — GitManager

Handles automatic Git staging and committing of healed locator files.

**Class: `GitManager`**

| Method                        | Purpose                                 |
|-------------------------------|-----------------------------------------|
| `init_repo(path)`             | Connect to or initialize a Git repo     |
| `commit_heal(file, name, url, provider)` | Stage + commit with standardized message |
| `get_current_branch()`        | Return active branch name               |
| `get_status()`                | Return branch, dirty state, modified files |

**Commit Message Format:**
```
[AI-HEAL] Updated locator for object: username_input on page: https://...

Provider: Gemini
Auto-healed by Loctor Builder
```

**Behavior:**
- Respects `auto_commit` setting (can be disabled)
- Gracefully handles missing repo or Git errors
- Converts absolute paths to repo-relative paths for staging

#### `core/script_loader.py` — ScriptLoader

Parses JSON automation script files into typed data models.

**Function: `load_script(file_path) → AutomationScript`**

**JSON Schema:**
```json
{
    "name": "Script Name",
    "base_url": "https://example.com",
    "metadata": { "author": "...", "version": "..." },
    "pages": [
        {
            "name": "Page Name",
            "url": "/path",
            "description": "...",
            "elements": [
                {
                    "name": "element_name",
                    "strategy": "id|css|xpath|name|class_name",
                    "value": "locator_expression",
                    "intent": "What this element is",
                    "line_number": 15,
                    "file_path": "path/to/source_file.py"
                }
            ]
        }
    ]
}
```

**Strategy Mapping:** Normalizes string names to `LocatorStrategy` enum (e.g., `"css_selector"` → `CSS`, `"class"` → `CLASS_NAME`).

#### `core/config_manager.py` — ConfigManager

Thread-safe singleton for centralized configuration with runtime hot-swapping.

**Class: `ConfigManager`**

| Method / Property           | Purpose                                    |
|-----------------------------|--------------------------------------------|
| `active_provider` (get/set) | Current AI provider with persistence       |
| `get_provider_config(name)` | Get model + API key for a provider         |
| `get_setting(key, default)` | Read a setting value                       |
| `set_setting(key, value)`   | Update a setting at runtime (persists)     |
| `get_all_providers()`       | List configured provider names             |
| `on_change(callback)`       | Register change notification callback      |
| `to_dict()`                 | Safe config copy (API keys `***REDACTED***`) |
| `reset()`                   | Reset singleton (for testing)              |

**Features:**
- **Singleton pattern** with `threading.Lock`
- **Thread-safe reads/writes** with `threading.RLock`
- **Environment variable overrides** (`.env` takes precedence over `config.json`)
- **Change callbacks** (used by dashboard for real-time updates)
- **Auto-save** to `config.json` on every mutation

**Override Hierarchy:**
```
Environment Variables (.env)     ← Highest priority
       ▼
config.json                      ← Base configuration
       ▼
Runtime set_setting() calls      ← Persisted immediately
```

---

### 5.3 AI Provider Layer

#### `ai/base_provider.py` — BaseAIProvider (Abstract)

Defines the contract that all AI providers must implement.

**Abstract Methods:**

| Method                  | Input                                               | Output         |
|-------------------------|-----------------------------------------------------|----------------|
| `generate_locators()`   | broken_locator, html, css, intent, url, screenshot  | `list[dict]`   |
| `analyze_element()`     | html, css, screenshot                               | `dict`         |

**Shared Methods:**

| Method                  | Purpose                                              |
|-------------------------|------------------------------------------------------|
| `_build_healing_prompt()` | Constructs the standardized prompt template         |
| `_encode_image(path)`   | Base64-encodes a screenshot for API consumption      |

**Prompt Template Structure:**
```
1. Role assignment: "You are an expert test automation engineer"
2. Context: Failed locator value, page URL, element intent
3. Evidence: Surrounding HTML snippet, computed CSS properties
4. Instructions: Generate exactly 3 candidates using different strategies
5. Output format: JSON array with {strategy, value, reasoning, confidence}
6. Constraints: Unique locators, prefer stable attributes, relative XPath only
```

**Expected AI Response Format:**
```json
[
    {
        "strategy": "id",
        "value": "username",
        "reasoning": "Stable ID attribute directly on the input element",
        "confidence": 0.95
    },
    {
        "strategy": "css",
        "value": "input#username[type='text']",
        "reasoning": "CSS selector combining tag, ID, and type for robustness",
        "confidence": 0.90
    },
    {
        "strategy": "xpath",
        "value": "//input[@id='username']",
        "reasoning": "Relative XPath targeting the unique ID attribute",
        "confidence": 0.85
    }
]
```

#### Provider Implementations

| Provider         | Class            | Model                       | Multimodal | Library              |
|------------------|------------------|-----------------------------|------------|----------------------|
| Google Gemini    | `GeminiProvider` | `gemini-2.5-pro`            | Yes        | `google-generativeai`|
| OpenAI           | `OpenAIProvider` | `gpt-4o`                    | Yes (Vision)| `openai`            |
| Anthropic Claude | `ClaudeProvider` | `claude-3-5-sonnet-20241022`| Yes        | `anthropic`          |

**All providers share:**
- Same prompt template (via `_build_healing_prompt()`)
- Same response parsing logic (JSON → list of dicts)
- Fallback parsing: raw JSON → strip code fences → extract `[...]` from text
- Multimodal support: text + screenshot image sent to the AI
- `temperature=0.2` for deterministic, reliable outputs

#### `ai/provider_factory.py` — ProviderFactory

Creates and caches provider instances using the Factory pattern.

**Class: `ProviderFactory`**

| Method                   | Purpose                                    |
|--------------------------|--------------------------------------------|
| `get_provider(name?)`    | Get cached instance (or create new one)    |
| `switch_provider(name)`  | Change active provider + return instance   |
| `clear_cache()`          | Clear all cached instances                 |

**Registry:**
```python
_PROVIDERS = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
}
```

**Validation:** Throws `ValueError` if API key is missing or still set to `"YOUR_KEY_HERE"`.

---

### 5.4 Data Models

All models use Python `dataclasses` with `to_dict()` serialization and `from_dict()` deserialization.

#### `models/locator.py`

```
LocatorStrategy (Enum)
├── XPATH
├── CSS
├── ID
├── NAME
├── CLASS_NAME
├── TAG_NAME
├── LINK_TEXT
└── PARTIAL_LINK_TEXT

LocatorStatus (Enum)
├── VALID
├── BROKEN
├── HEALED
└── UNVERIFIED

Locator (Dataclass)
├── strategy: LocatorStrategy
├── value: str
├── object_name: str
├── description: str
├── status: LocatorStatus
├── confidence: float
├── last_verified: Optional[datetime]
└── selector_string (property): "strategy=value"

LocatorCandidate (Dataclass)
├── locator: Locator
├── rank: int
├── ai_provider: str
├── reasoning: str
├── visibility_score: float
└── validated: bool

LocatorCandidateList (Dataclass)
├── broken_locator: Locator
├── candidates: list[LocatorCandidate]
├── selected: Optional[LocatorCandidate]
├── timestamp: datetime
├── add_candidate(candidate)
└── select_best() → Optional[LocatorCandidate]  # highest visibility_score among validated
```

#### `models/page_object.py`

```
PageElement (Dataclass)
├── name: str
├── locator: Locator
├── intent: str
├── page_name: str
├── line_number: Optional[int]
└── file_path: Optional[str]

PageObject (Dataclass)
├── name: str
├── url: str
├── elements: list[PageElement]
└── description: str

AutomationScript (Dataclass)
├── name: str
├── file_path: str
├── base_url: str
├── pages: list[PageObject]
├── metadata: dict
└── total_elements (property): sum of all page elements
```

#### `models/audit_result.py`

```
AuditStatus (Enum)
├── PASSED
├── FAILED
├── HEALED
└── SKIPPED

ForensicEvidence (Dataclass)
├── full_page_screenshot: Optional[str]
├── target_area_screenshot: Optional[str]
├── dom_snapshot_path: Optional[str]
├── html_snippet: str
├── css_properties: dict
├── page_url: str
├── page_title: str
├── viewport_size: dict
└── timestamp: datetime

ElementAuditResult (Dataclass)
├── element_name: str
├── page_name: str
├── original_locator: Locator
├── status: AuditStatus
├── healed_locator: Optional[LocatorCandidate]
├── forensic_evidence: Optional[ForensicEvidence]
├── error_message: str
├── healing_attempts: int
└── timestamp: datetime

AuditReport (Dataclass)
├── script_name: str
├── start_time: datetime
├── end_time: Optional[datetime]
├── results: list[ElementAuditResult]
├── ai_provider_used: str
├── total_elements (property)
├── passed (property)
├── failed (property)
├── healed (property)
└── success_rate (property): (passed + healed) / total × 100
```

---

### 5.5 Web Dashboard (UI)

**Technology:** Flask + Flask-SocketIO with inline HTML/CSS/JS (single-file SPA)

**Theme:** Dark mode with CSS custom properties

| Route              | Method | Purpose                          |
|--------------------|--------|----------------------------------|
| `/`                | GET    | Serve the dashboard HTML         |
| `/api/config`      | GET    | Return redacted config as JSON   |
| `/api/provider`    | POST   | Switch active AI provider        |
| `/api/settings`    | POST   | Update a runtime setting         |
| `/api/stats`       | GET    | System status endpoint           |

**WebSocket Events (SocketIO):**

| Event              | Direction      | Purpose                          |
|--------------------|----------------|----------------------------------|
| `config_updated`   | Server → Client| Config change notification       |
| `element_audited`  | Server → Client| Real-time element audit result   |
| `page_started`     | Server → Client| Page navigation event            |

**Dashboard Features:**
- Provider switching (3 buttons: Gemini, OpenAI, Claude)
- Live statistics grid (Total, Passed, Healed, Failed)
- Settings panel (auto-commit toggle, headless toggle, retry limit, timeout)
- Configuration viewer (keys redacted)
- Live activity feed with timestamps and color-coded entries
- Connection status indicator with pulse animation

---

### 5.6 Input Layer

#### Automation Scripts (`input/scripts/`)

JSON files that define what to audit. Each script specifies:
- A target website (`base_url`)
- One or more pages to navigate
- Elements on each page with their expected locators
- Source file paths for locator updates

#### Page Objects (`input/page_objects/`)

Sample Selenium Page Object files using the `By` locator pattern. These are the **source files** that the system modifies when healing a locator.

**Pattern used:**
```python
class LoginPage:
    USERNAME_INPUT = (By.ID, "username")       # ← locator defined here
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button.radius")

    def enter_username(self, username):
        self.driver.find_element(*self.USERNAME_INPUT).send_keys(username)
```

---

## 6. Data Flow & Sequence Diagrams

### 6.1 End-to-End Audit Flow

```
User
 │
 ├── CLI: python main.py audit input/scripts/02_broken.json --provider gemini
 │   OR
 └── Dashboard: POST /api/provider + trigger audit
         │
         ▼
    ┌─────────┐
    │ main.py │ → setup_logging() → ConfigManager("config.json")
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  cli.py │ → parse args → create Auditor(config) → set callbacks
    └────┬────┘
         │
         ▼
    ┌──────────┐
    │ Auditor  │ → load_script("02_broken.json") → AutomationScript
    └────┬─────┘
         │
         ├── BrowserEngine.start()  →  Launch Chromium
         │
         │   ┌────── FOR EACH PAGE ──────────────────────────────────────┐
         │   │                                                           │
         │   │  BrowserEngine.navigate(base_url + page.url)             │
         │   │  callback: on_page_started(page_name, url)               │
         │   │                                                           │
         │   │   ┌────── FOR EACH ELEMENT ────────────────────────────┐  │
         │   │   │                                                     │  │
         │   │   │  _audit_element(element, url)                      │  │
         │   │   │    │                                                │  │
         │   │   │    ├── find_element(locator) → Found?              │  │
         │   │   │    │   ├── YES + visibility ≥ 0.3 → PASSED ✓      │  │
         │   │   │    │   └── NO or visibility < 0.3:                 │  │
         │   │   │    │                                                │  │
         │   │   │    └── HealingEngine.heal_element(element, url)    │  │
         │   │   │        └── (see §6.2 for details)                  │  │
         │   │   │              │                                      │  │
         │   │   │              ├── HEALED → _apply_heal()            │  │
         │   │   │              │   ├── FileModifier.update_file()    │  │
         │   │   │              │   └── GitManager.commit_heal()      │  │
         │   │   │              │                                      │  │
         │   │   │              └── FAILED → log error                │  │
         │   │   │                                                     │  │
         │   │   │  Append result to AuditReport                      │  │
         │   │   │  callback: on_element_audited(result)              │  │
         │   │   └─────────────────────────────────────────────────────┘  │
         │   └───────────────────────────────────────────────────────────┘
         │
         ├── BrowserEngine.stop()
         ├── _save_report("script_name") → logs/reports/audit_<name>_<ts>.json
         └── Return AuditReport to CLI → _print_summary()
```

### 6.2 Self-Healing Pipeline

```
HealingEngine.heal_element(element, page_url)
    │
    ├── Get AI provider from ProviderFactory
    │
    ├── ForensicAgent.collect_evidence(locator, page_name)
    │   ├── Capture full-page screenshot      → logs/screenshots/..._full_page.png
    │   ├── Capture target area screenshot     → logs/screenshots/..._target_area.png
    │   ├── Capture DOM snapshot               → logs/dom/..._DOM_structure.html
    │   ├── Get surrounding HTML               → string (parent HTML or body[:5000])
    │   └── Get surrounding elements CSS       → dict (up to 10 interactive elements)
    │
    │   ┌────── RETRY LOOP (up to retry_limit=3) ──────────────────────────┐
    │   │                                                                    │
    │   │  AI Provider.generate_locators(                                   │
    │   │      broken_locator = "id=txt_username_BROKEN",                   │
    │   │      html_snippet   = "<div id='login'>...<input id='username'>", │
    │   │      css_properties = { "input#username": { display: "block" } }, │
    │   │      intent         = "Username text input field",                │
    │   │      page_url       = "https://the-internet.herokuapp.com/login", │
    │   │      screenshot     = "logs/screenshots/..._full_page.png"        │
    │   │  )                                                                │
    │   │     │                                                              │
    │   │     ▼                                                              │
    │   │  AI Returns: [ {strategy, value, reasoning, confidence}, ... ]    │
    │   │     │                                                              │
    │   │     ▼                                                              │
    │   │  LocatorValidator.build_candidate_list(broken, suggestions, name) │
    │   │     │                                                              │
    │   │     ▼                                                              │
    │   │  LocatorValidator.validate_candidates(candidates, url)            │
    │   │     │                                                              │
    │   │     ├── Candidate validated? → Return HEALED result               │
    │   │     └── No valid candidate?  → Continue loop                      │
    │   │                                                                    │
    │   └──────────────────────────────────────────────────────────────────┘
    │
    └── All retries exhausted → Return FAILED result
```

### 6.3 Candidate Validation Flow

```
validate_candidates(candidate_list, page_url)
    │
    │   FOR EACH candidate in candidate_list.candidates:
    │   │
    │   ├── KnownLocatorsDB.is_duplicate(strategy, value)?
    │   │   └── YES + different object_name → SKIP (prevent cross-assignment)
    │   │
    │   ├── BrowserEngine.find_element_raw(strategy, value)
    │   │   └── NOT FOUND → candidate.validated = False → NEXT
    │   │
    │   ├── BrowserEngine.get_element_visibility_score(element)
    │   │   └── score < 0.3 → candidate.validated = False → NEXT
    │   │
    │   └── score ≥ 0.3 → candidate.validated = True
    │                      candidate.locator.status = HEALED
    │
    ├── Select best: max(validated candidates, key=visibility_score)
    │
    ├── IF selected:
    │   └── KnownLocatorsDB.add_locator(strategy, value, object, url, "ai-healed-gemini")
    │
    └── Return selected (or None)
```

---

## 7. Design Patterns

| Pattern            | Where Used                                    | Purpose                                     |
|--------------------|-----------------------------------------------|---------------------------------------------|
| **Singleton**      | `ConfigManager`                               | Single source of truth for configuration    |
| **Factory**        | `ProviderFactory`                             | Create/cache AI provider instances          |
| **Strategy**       | `BaseAIProvider` + implementations            | Interchangeable AI backends                 |
| **Template Method**| `BaseAIProvider._build_healing_prompt()`      | Shared prompt structure, custom API calls   |
| **Observer**       | `ConfigManager.on_change()` + callbacks       | React to config changes (dashboard updates) |
| **Facade**         | `Auditor`                                     | Simplified interface over complex subsystems|
| **Repository**     | `KnownLocatorsDB`                             | Abstract data access (TinyDB)               |
| **Adapter**        | `BrowserEngine._raw_to_playwright_selector()` | Translate locator strategies to Playwright  |
| **Decorator**      | `FileModifier._build_comment()`               | Add metadata comments to healed code        |

---

## 8. Configuration System

### Configuration Sources (Priority Order)

```
┌──────────────────────────────┐
│  1. Environment Variables    │  ← Highest priority
│     (.env file loaded via    │
│      python-dotenv)          │
│                              │
│  GEMINI_API_KEY=your_key...  │
│  ACTIVE_PROVIDER=gemini      │
│  HEADLESS=true               │
├──────────────────────────────┤
│  2. config.json              │  ← Base configuration
│                              │
│  {                           │
│    "active_provider": "...", │
│    "providers": {...},       │
│    "settings": {...}         │
│  }                           │
├──────────────────────────────┤
│  3. Runtime API              │  ← CLI/Dashboard updates
│                              │
│  config.set_setting(k, v)    │
│  config.active_provider = x  │
│  (persists to config.json)   │
└──────────────────────────────┘
```

### Full Settings Reference

| Setting               | Type    | Default                      | Description                                   |
|-----------------------|---------|------------------------------|-----------------------------------------------|
| `active_provider`     | string  | `"gemini"`                   | Active AI provider                            |
| `screenshot_path`     | string  | `"./logs/screenshots"`       | Directory for forensic screenshots            |
| `dom_capture_path`    | string  | `"./logs/dom"`               | Directory for DOM snapshots                   |
| `auto_commit`         | bool    | `true`                       | Auto-commit healed files to Git               |
| `retry_limit`         | int     | `3`                          | Max AI healing attempts per element           |
| `validation_timeout`  | int     | `5000`                       | Element wait timeout (ms)                     |
| `headless`            | bool    | `true`                       | Run browser in headless mode                  |
| `browser`             | string  | `"chromium"`                 | Browser engine (chromium/firefox/webkit)       |
| `viewport_width`      | int     | `1920`                       | Browser viewport width                        |
| `viewport_height`     | int     | `1080`                       | Browser viewport height                       |
| `known_locators_db`   | string  | `"./data/known_locators.json"` | Path to TinyDB database                    |
| `log_level`           | string  | `"INFO"`                     | Logging level (DEBUG/INFO/WARNING/ERROR)      |
| `dashboard_port`      | int     | `5050`                       | Web dashboard port                            |

---

## 9. AI Provider Architecture

### Provider Class Hierarchy

```
            BaseAIProvider (ABC)
            ├── model: str
            ├── api_key: str
            ├── name: str (property)
            │
            ├── generate_locators()  [abstract]
            ├── analyze_element()    [abstract]
            ├── _build_healing_prompt()
            └── _encode_image()
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
  GeminiProvider  OpenAI     Claude
                 Provider    Provider
```

### Provider Comparison

| Feature              | Gemini                     | OpenAI                      | Claude                     |
|----------------------|----------------------------|-----------------------------|----------------------------|
| **Model**            | gemini-2.5-pro             | gpt-4o                      | claude-3-5-sonnet-20241022 |
| **Library**          | google-generativeai        | openai (async)              | anthropic (async)          |
| **Image Input**      | Inline bytes (mime_type)   | Base64 data URL             | Base64 source block        |
| **Temperature**      | 0.2                        | 0.2                         | 0.2                        |
| **Max Tokens**       | 2048                       | 2048                        | 2048                       |
| **Async Method**     | `generate_content_async()` | `chat.completions.create()` | `messages.create()`        |
| **Response Parsing** | Shared JSON extraction with code-fence stripping                                     |

### Runtime Provider Switching

```
User: python main.py switch openai
  │
  ├── CLI: config.active_provider = "openai"
  │         │
  │         ├── ConfigManager validates provider name
  │         ├── Updates in-memory config
  │         ├── Persists to config.json
  │         └── Notifies callbacks ("provider_changed", "openai")
  │
  └── Next audit will use ProviderFactory.get_provider()
      └── Creates/returns cached OpenAIProvider instance
```

---

## 10. Browser Automation Layer

### Technology: Playwright (Async API)

```
BrowserEngine
├── _playwright    → Playwright instance
├── _browser       → Browser instance (Chromium/Firefox/WebKit)
├── _context       → BrowserContext (isolated, custom viewport)
└── _page          → Page (single tab, all operations here)
```

### Lifecycle

```
start()
  └── async_playwright().start()
      └── chromium.launch(headless=True)
          └── browser.new_context(viewport={1920x1080})
              └── context.new_page()

navigate(url)
  └── page.goto(url, wait_until="networkidle", timeout=15000)

find_element(locator)
  └── page.wait_for_selector(selector, timeout=5000, state="attached")
      └── page.query_selector(selector)

stop()
  └── context.close() → browser.close() → playwright.stop()
```

### Navigation Wait Strategy
- Uses `networkidle` (no network requests for 500ms)
- Timeout: `validation_timeout × 3` (default: 15000ms for navigation)
- Element timeout: `validation_timeout` (default: 5000ms)

---

## 11. Persistence & Storage

### Storage Locations

| Data                  | Format  | Location                                | Git-tracked |
|-----------------------|---------|-----------------------------------------|-------------|
| Configuration         | JSON    | `config.json`                           | Yes         |
| API Keys              | dotenv  | `.env`                                  | No          |
| Known Locators DB     | JSON    | `data/known_locators.json`              | No          |
| Audit Reports         | JSON    | `logs/reports/audit_<name>_<ts>.json`   | No          |
| Screenshots           | PNG     | `logs/screenshots/`                     | No          |
| DOM Snapshots         | HTML    | `logs/dom/`                             | No          |
| Application Log       | Text    | `logs/loctor_builder.log`               | No          |
| Test Runner Log       | Text    | `logs/test_runner.log`                  | No          |

### Audit Report JSON Structure

```json
{
    "script_name": "HerokuApp Broken Locators",
    "start_time": "2026-02-16T14:30:00",
    "end_time": "2026-02-16T14:30:45",
    "total_elements": 4,
    "passed": 2,
    "failed": 0,
    "healed": 2,
    "success_rate": 100.0,
    "ai_provider_used": "gemini",
    "results": [
        {
            "element_name": "username_input",
            "page_name": "Login Page",
            "original_locator": {
                "strategy": "id",
                "value": "txt_username_BROKEN",
                "status": "broken"
            },
            "status": "healed",
            "healed_locator": {
                "locator": {
                    "strategy": "id",
                    "value": "username",
                    "confidence": 0.95
                },
                "rank": 1,
                "ai_provider": "Gemini",
                "reasoning": "Stable ID attribute",
                "visibility_score": 1.0,
                "validated": true
            },
            "forensic_evidence": {
                "full_page_screenshot": "logs/screenshots/..._full_page.png",
                "dom_snapshot_path": "logs/dom/..._DOM_structure.html",
                "html_snippet": "<div id='login'>..."
            },
            "healing_attempts": 1
        }
    ]
}
```

---

## 12. Error Handling Strategy

### Error Categories & Responses

| Category               | Example                              | Handling                                  |
|------------------------|--------------------------------------|-------------------------------------------|
| **Configuration**      | Config file not found                | `FileNotFoundError` raised immediately    |
| **Script Loading**     | Invalid JSON or missing fields       | `FileNotFoundError` + validation errors   |
| **Browser**            | Launch failure, navigation timeout   | Logged, elements marked SKIPPED           |
| **Element Not Found**  | Locator doesn't match any element    | Triggers healing pipeline                 |
| **AI API Error**       | Rate limit (429), server error (500) | Logged, retry on next attempt             |
| **AI Response Parsing**| Malformed JSON from AI               | Cascading fallback: raw → strip fences → extract array → empty list |
| **File I/O**           | Source file not found / write error  | Logged, heal still recorded but not persisted |
| **Git**                | Commit failure, no repo              | Logged, audit continues without commit    |
| **Duplicate Locator**  | Same locator for different element   | Candidate skipped, next candidate tested  |

### Error Handling Pattern

```python
# Core pattern used throughout the codebase:
try:
    result = await risky_operation()
except SpecificError as e:
    logger.error("Descriptive message: %s", e)
    return graceful_fallback
except Exception as e:
    logger.error("Unexpected error in <context>: %s", e)
    return safe_default
```

### Resilience Features

1. **Retry logic**: Healing attempts up to `retry_limit` (default 3)
2. **Graceful degradation**: Screenshot failure doesn't block healing
3. **Fallback parsing**: Multiple JSON parsing strategies for AI responses
4. **Page-level isolation**: One page failure doesn't skip other pages
5. **Element-level isolation**: One element failure doesn't skip other elements
6. **Git independence**: Audit works even without a Git repository

---

## 13. Logging & Reporting

### Logging Configuration

| Destination            | Format                                                    |
|------------------------|-----------------------------------------------------------|
| Console (stdout)       | `2026-02-16 14:30:00 [INFO] core.auditor: message`       |
| File                   | `logs/loctor_builder.log` (same format, UTF-8)            |

### Log Levels by Component

| Component        | DEBUG                           | INFO                         | WARNING                        | ERROR                        |
|------------------|---------------------------------|------------------------------|--------------------------------|------------------------------|
| Auditor          | —                               | Start/end audit, page nav    | —                              | Navigation failure           |
| BrowserEngine    | Element not found (debug)       | Browser start/stop, navigate | —                              | —                            |
| ForensicAgent    | —                               | Evidence collected, DOM saved | Screenshot capture failure     | DOM capture failure          |
| HealingEngine    | —                               | Healing start, attempts, success | No suggestions from AI     | AI API errors                |
| LocatorValidator | Candidate test results          | Candidate pass, best selected| Duplicate skipped, invalid suggestion | —                    |
| FileModifier     | —                               | Line updated, file saved     | Locator not found in file      | File read/write errors       |
| GitManager       | —                               | Repo connected, commit SHA   | No repo, auto-commit disabled  | Commit failure               |
| ConfigManager    | —                               | —                            | —                              | Config file missing          |
| Providers        | —                               | —                            | JSON parse failure (fallback)  | API call failure             |

---

## 14. External Dependencies

### Runtime Dependencies

| Package              | Version     | Purpose                                     |
|----------------------|-------------|---------------------------------------------|
| `playwright`         | ≥ 1.49.0   | Browser automation (Chromium/Firefox/WebKit) |
| `google-generativeai`| ≥ 0.8.0    | Google Gemini AI API client                 |
| `openai`             | ≥ 1.58.0   | OpenAI GPT-4o API client                   |
| `anthropic`          | ≥ 0.40.0   | Anthropic Claude API client                 |
| `tinydb`             | ≥ 4.8.2    | Lightweight JSON document database          |
| `gitpython`          | ≥ 3.1.43   | Git operations (stage, commit, status)      |
| `flask`              | ≥ 3.1.0    | Web dashboard HTTP server                   |
| `flask-socketio`     | ≥ 5.4.0    | Real-time WebSocket communication           |
| `click`              | ≥ 8.1.7    | CLI framework (command groups, options)      |
| `rich`               | ≥ 13.9.0   | Terminal formatting (tables, panels, colors) |
| `python-dotenv`      | ≥ 1.0.1    | Load `.env` files into environment          |
| `pyyaml`             | ≥ 6.0.2    | YAML configuration support                  |
| `aiohttp`            | ≥ 3.11.0   | Async HTTP client                           |
| `aiofiles`           | ≥ 24.1.0   | Async file operations                       |
| `jinja2`             | ≥ 3.1.4    | HTML template rendering                     |
| `Pillow`             | ≥ 11.0.0   | Image processing (screenshots)              |
| `cssutils`           | ≥ 2.11.1   | CSS parsing utilities                       |
| `lxml`               | ≥ 5.3.0    | XML/HTML parsing                            |

### System Requirements

| Requirement          | Details                                          |
|----------------------|--------------------------------------------------|
| Python               | 3.10+                                            |
| Playwright browsers  | Install via `playwright install`                 |
| OS                   | Windows, macOS, Linux                            |
| Network              | Internet access for AI APIs + target web pages   |

---

## 15. Security Considerations

### API Key Management

| Practice                            | Implementation                                    |
|-------------------------------------|---------------------------------------------------|
| Keys in `.env` (git-ignored)        | `.gitignore` includes `.env`, `*.env`             |
| Env vars override config file       | `ConfigManager._apply_env_overrides()`            |
| Redaction in API responses          | `ConfigManager.to_dict()` replaces with `***REDACTED***` |
| Redaction in dashboard              | `/api/config` returns redacted keys               |
| Placeholder detection               | `ProviderFactory` rejects `"YOUR_KEY_HERE"`      |

### Files Excluded from Git

```gitignore
.env                    # API keys and secrets
*.env                   # Any env files
config_local.json       # Local config overrides
logs/                   # Screenshots, DOM, reports, logs
data/                   # TinyDB database
__pycache__/            # Python bytecode
```

### Recommendations

1. Rotate API keys if exposed in logs or conversations
2. Use environment variables over `config.json` for API keys in production
3. The dashboard has no authentication — run only on trusted networks
4. `auto_commit` should be disabled in shared/CI environments to prevent unreviewed commits

---

## 16. Extensibility Guide

### Adding a New AI Provider

1. Create `ai/new_provider.py`:
```python
from ai.base_provider import BaseAIProvider

class NewProvider(BaseAIProvider):
    def __init__(self, model: str, api_key: str):
        super().__init__(model, api_key)
        self._name = "NewProvider"

    async def generate_locators(self, **kwargs) -> list[dict]:
        prompt = self._build_healing_prompt(...)
        # Call your API
        return self._parse_response(response_text)

    async def analyze_element(self, **kwargs) -> dict:
        # Implementation
        pass
```

2. Register in `ai/provider_factory.py`:
```python
from ai.new_provider import NewProvider
_PROVIDERS["new_provider"] = NewProvider
```

3. Add config in `config.json`:
```json
"new_provider": { "model": "model-name", "api_key": "YOUR_KEY_HERE" }
```

4. Add env var mapping in `core/config_manager.py`:
```python
"new_provider": "NEW_PROVIDER_API_KEY"
```

### Adding a New Locator Strategy

1. Add to `LocatorStrategy` enum in `models/locator.py`
2. Add mapping in `core/script_loader.py` → `STRATEGY_MAP`
3. Add translation in `core/browser_engine.py` → `_raw_to_playwright_selector()`
4. Add mapping in `core/locator_validator.py` → `_parse_strategy()`

### Adding a New Dashboard Widget

1. Add HTML to the `TEMPLATE` string in `ui/dashboard.py`
2. Add CSS in the `<style>` block
3. Add JavaScript event handlers
4. Optionally add a new `/api/` route and SocketIO event

---

*Document generated from source code analysis on 2026-02-16.*
