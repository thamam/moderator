# QA Setup Guide

Comprehensive guide for installing, configuring, and using the Quality Assurance (QA) integration in Moderator.

**Audience:** Developers setting up QA tools for automated code quality gates in PR review workflows.

**Prerequisites:**
- Python 3.9+ installed
- Moderator system installed (see [README.md](../README.md))
- Basic understanding of YAML configuration

---

## Table of Contents

1. [Installation](#installation)
   - [Windows](#windows-installation)
   - [macOS](#macos-installation)
   - [Linux](#linux-installation)
   - [Verification](#verification)
2. [Tool-Specific Configuration](#tool-specific-configuration)
   - [Pylint Configuration](#pylint-configuration)
   - [Flake8 Configuration](#flake8-configuration)
   - [Bandit Configuration](#bandit-configuration)
3. [Project-Type Configurations](#project-type-configurations)
   - [Web Application](#web-application-project)
   - [Data Science](#data-science-project)
   - [CLI Tool](#cli-tool-project)
   - [Library/Package](#librarypackage-project)
4. [Score Weighting](#score-weighting)
   - [Equal Weights (Default)](#equal-weights-default)
   - [Security-Focused](#security-focused-weights)
   - [Code Quality-Focused](#code-quality-focused-weights)
5. [Report Interpretation](#report-interpretation)
   - [Understanding QA Reports](#understanding-qa-reports)
   - [Example Reports](#example-reports)
   - [Acting on Feedback](#acting-on-feedback)
6. [Advanced Configuration](#advanced-configuration)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### Windows Installation

**Option 1: Using pip (Recommended)**

```powershell
# Open PowerShell or Command Prompt

# Install all tools
pip install pylint flake8 bandit

# Or use virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate
pip install pylint flake8 bandit

# Verify installation
pylint --version
flake8 --version
bandit --version
```

**Option 2: Using Conda**

```powershell
# If using Anaconda/Miniconda
conda install -c conda-forge pylint flake8
pip install bandit  # bandit not in conda-forge, use pip
```

**Common Windows Issues:**

- **PATH not set:** Ensure Python Scripts directory is in PATH
  ```powershell
  # Add to PATH (PowerShell, run as Administrator)
  $env:Path += ";C:\Python39\Scripts"
  ```

- **Permission denied:** Run PowerShell as Administrator

### macOS Installation

**Option 1: Using pip (Recommended)**

```bash
# Using system Python
pip3 install pylint flake8 bandit

# Or using virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install pylint flake8 bandit

# Verify installation
pylint --version
flake8 --version
bandit --version
```

**Option 2: Using Homebrew**

```bash
# Install Python via Homebrew first (if needed)
brew install python

# Install tools
pip3 install pylint flake8 bandit
```

**Common macOS Issues:**

- **Command not found:** Ensure pip is in PATH
  ```bash
  # Add to ~/.zshrc or ~/.bash_profile
  export PATH="$HOME/Library/Python/3.9/bin:$PATH"
  source ~/.zshrc  # or source ~/.bash_profile
  ```

- **Permission errors:** Use `--user` flag or virtual environment
  ```bash
  pip3 install --user pylint flake8 bandit
  ```

### Linux Installation

**Ubuntu/Debian:**

```bash
# System package manager (may have older versions)
sudo apt-get update
sudo apt-get install pylint python3-flake8 bandit

# Or use pip for latest versions (recommended)
pip3 install pylint flake8 bandit

# With virtual environment (best practice)
python3 -m venv venv
source venv/bin/activate
pip install pylint flake8 bandit
```

**Fedora/CentOS/RHEL:**

```bash
# System package manager
sudo dnf install pylint python3-flake8
pip3 install bandit

# Or use pip for all tools
pip3 install pylint flake8 bandit
```

**Arch Linux:**

```bash
# System package manager
sudo pacman -S python-pylint python-flake8 python-bandit

# Or use pip
pip install pylint flake8 bandit
```

### Verification

After installation, verify all tools are accessible:

```bash
# Check versions
pylint --version   # Should show 2.x or 3.x
flake8 --version   # Should show 5.x or 6.x
bandit --version   # Should show 1.7.x or higher

# Test on sample file
echo "print('hello world')" > test.py

# Run each tool
pylint test.py    # Should analyze successfully
flake8 test.py    # Should analyze successfully
bandit test.py    # Should analyze successfully

# Clean up
rm test.py
```

**Expected Output:**

```
$ pylint --version
pylint 3.0.2

$ flake8 --version
6.1.0 (mccabe: 0.7.0, pycodestyle: 2.11.0, pyflakes: 3.1.0)

$ bandit --version
bandit 1.7.5
```

---

## Tool-Specific Configuration

### Pylint Configuration

**What Pylint Checks:**
- Code quality and design patterns
- PEP 8 style violations
- Potential bugs and errors
- Code complexity and maintainability
- Documentation completeness

**Default Moderator Config:**

```yaml
gear3:
  qa:
    tools: [pylint]
```

**Per-Tool Configuration (Advanced):**

Create `.pylintrc` in your project root:

```ini
[MASTER]
# Maximum number of parallel jobs (use all cores)
jobs=0

[MESSAGES CONTROL]
# Disable specific checks (comma-separated IDs)
disable=
    C0111,  # missing-docstring
    C0103,  # invalid-name
    R0903   # too-few-public-methods

[FORMAT]
# Maximum line length
max-line-length=100

# Maximum number of lines in a module
max-module-lines=1000

[DESIGN]
# Maximum number of arguments for function
max-args=7

# Maximum number of local variables
max-locals=15
```

**Common Pylint Customizations:**

```yaml
# Moderator config.yaml - minimal pylint warnings
gear3:
  qa:
    tools: [pylint]
    thresholds:
      error_count: 0       # Block on errors only
      warning_count: null  # Unlimited warnings
      minimum_score: 70.0  # Lower threshold for pylint
```

### Flake8 Configuration

**What Flake8 Checks:**
- PEP 8 style guide compliance
- Logical errors (pyflakes)
- Code complexity (mccabe)
- Unused imports and variables

**Default Moderator Config:**

```yaml
gear3:
  qa:
    tools: [flake8]
```

**Per-Tool Configuration (Advanced):**

Create `.flake8` in your project root:

```ini
[flake8]
# Maximum line length
max-line-length = 100

# Maximum code complexity (default: 10)
max-complexity = 15

# Ignore specific error codes
ignore =
    E203,  # whitespace before ':'
    E501,  # line too long (covered by max-line-length)
    W503   # line break before binary operator

# Exclude directories
exclude =
    .git,
    __pycache__,
    venv,
    .venv,
    build,
    dist

# Per-file ignores
per-file-ignores =
    __init__.py:F401  # Allow unused imports in __init__.py
```

**Common Flake8 Customizations:**

```yaml
# Moderator config.yaml - lenient style checking
gear3:
  qa:
    tools: [flake8]
    thresholds:
      error_count: 0       # Block on errors
      warning_count: 20    # Allow up to 20 style warnings
```

### Bandit Configuration

**What Bandit Checks:**
- Security vulnerabilities
- Hardcoded passwords and secrets
- SQL injection risks
- Insecure cryptographic practices
- Unsafe file operations

**Default Moderator Config:**

```yaml
gear3:
  qa:
    tools: [bandit]
```

**Per-Tool Configuration (Advanced):**

Create `.bandit` in your project root:

```yaml
# .bandit
exclude_dirs:
  - /test
  - /tests
  - /venv

# Tests to skip (by ID)
skips:
  - B101  # assert_used (common in tests)
  - B601  # paramiko_calls (if using paramiko library)

# Severity levels to report
# Options: LOW, MEDIUM, HIGH
level: MEDIUM

# Confidence levels to report
# Options: LOW, MEDIUM, HIGH
confidence: MEDIUM
```

**Common Bandit Customizations:**

```yaml
# Moderator config.yaml - strict security scanning
gear3:
  qa:
    tools: [bandit]
    thresholds:
      error_count: 0       # Zero tolerance for security issues
      warning_count: 0     # Block on medium/low findings too
      minimum_score: 95.0  # High bar for security
    tool_weights:
      bandit: 2.0          # Double weight for security
```

---

## Project-Type Configurations

### Web Application Project

**Characteristics:**
- Django/Flask/FastAPI codebases
- Multiple dependencies and imports
- Complex routing and views
- Database models and migrations

**Recommended Configuration:**

```yaml
# config/config.yaml
gear3:
  qa:
    tools: [pylint, flake8, bandit]

    thresholds:
      error_count: 0        # No errors (critical bugs)
      warning_count: 30     # Allow some warnings (style issues)
      minimum_score: 75.0   # Moderate quality bar

    tool_weights:
      bandit: 1.5   # Prioritize security (web apps at risk)
      pylint: 1.0   # Standard code quality
      flake8: 0.8   # Style less critical for web apps
```

**Rationale:**
- Security is paramount for web apps → higher bandit weight
- Allow more warnings due to framework boilerplate code
- Focus on eliminating critical errors and security issues

### Data Science Project

**Characteristics:**
- Jupyter notebooks
- Heavy use of numpy/pandas/matplotlib
- Exploratory code with experimentation
- Often single-file scripts

**Recommended Configuration:**

```yaml
# config/config.yaml
gear3:
  qa:
    tools: [pylint]  # Minimal - avoid style pedantry

    thresholds:
      error_count: 5        # Allow some errors (exploratory code)
      warning_count: null   # Unlimited warnings
      minimum_score: 60.0   # Low bar for data science

    tool_weights:
      pylint: 1.0
```

**Rationale:**
- Data science code is often experimental and quick iterations
- Focus on critical errors only, not style perfection
- Single tool (pylint) to avoid noise from multiple linters

### CLI Tool Project

**Characteristics:**
- Command-line interface
- Argument parsing
- File I/O operations
- Minimal dependencies

**Recommended Configuration:**

```yaml
# config/config.yaml
gear3:
  qa:
    tools: [pylint, flake8, bandit]

    thresholds:
      error_count: 0        # Zero errors
      warning_count: 10     # Few warnings allowed
      minimum_score: 85.0   # High quality bar

    tool_weights:
      pylint: 1.2   # Emphasize code quality
      flake8: 1.0   # Standard style checking
      bandit: 0.8   # Security less critical for CLI tools
```

**Rationale:**
- CLI tools are often distributed → high quality needed
- Focus on code quality and maintainability
- Security less critical than web apps (but still checked)

### Library/Package Project

**Characteristics:**
- Public API surface
- Extensive documentation
- Comprehensive tests
- Distributed to other developers

**Recommended Configuration:**

```yaml
# config/config.yaml
gear3:
  qa:
    tools: [pylint, flake8, bandit]

    thresholds:
      error_count: 0        # Zero tolerance
      warning_count: 0      # Zero tolerance for warnings too
      minimum_score: 90.0   # Very high bar

    tool_weights:
      pylint: 1.0   # Code quality critical
      flake8: 1.0   # Style consistency critical
      bandit: 1.0   # Security matters for libraries

    fail_on_error: true
```

**Rationale:**
- Libraries have external consumers → highest quality standards
- Zero tolerance for both errors and warnings
- Equal weight for all aspects (quality, style, security)

---

## Score Weighting

### Equal Weights (Default)

All tools contribute equally to overall score:

```yaml
gear3:
  qa:
    tools: [pylint, flake8, bandit]
    tool_weights:
      pylint: 1.0
      flake8: 1.0
      bandit: 1.0
```

**Score Calculation:**

```
overall_score = (pylint_score × 1.0 + flake8_score × 1.0 + bandit_score × 1.0) / 3.0

Example:
  pylint: 85, flake8: 80, bandit: 90
  overall = (85 × 1 + 80 × 1 + 90 × 1) / 3 = 85.0
```

### Security-Focused Weights

Prioritize security findings over style issues:

```yaml
gear3:
  qa:
    tools: [pylint, flake8, bandit]
    tool_weights:
      bandit: 2.0   # Security counts double
      pylint: 1.0   # Standard weight
      flake8: 0.5   # Style counts half
```

**Score Calculation:**

```
overall_score = (pylint × 1.0 + flake8 × 0.5 + bandit × 2.0) / (1.0 + 0.5 + 2.0)

Example:
  pylint: 85, flake8: 70, bandit: 95
  overall = (85 × 1 + 70 × 0.5 + 95 × 2) / 3.5
          = (85 + 35 + 190) / 3.5
          = 310 / 3.5
          = 88.6
```

**Use Case:** Web applications, APIs, security-critical systems

### Code Quality-Focused Weights

Prioritize code quality and maintainability:

```yaml
gear3:
  qa:
    tools: [pylint, flake8, bandit]
    tool_weights:
      pylint: 2.0   # Quality counts double
      flake8: 1.0   # Standard weight
      bandit: 0.5   # Security counts half
```

**Score Calculation:**

```
overall_score = (pylint × 2.0 + flake8 × 1.0 + bandit × 0.5) / (2.0 + 1.0 + 0.5)

Example:
  pylint: 90, flake8: 85, bandit: 70
  overall = (90 × 2 + 85 × 1 + 70 × 0.5) / 3.5
          = (180 + 85 + 35) / 3.5
          = 300 / 3.5
          = 85.7
```

**Use Case:** Libraries, SDKs, maintainability-critical projects

---

## Report Interpretation

### Understanding QA Reports

QA reports contain:

1. **Summary Section**
   - Overall score (0-100)
   - Tools run
   - Total issues count
   - Breakdown by severity (errors, warnings, info)

2. **Per-Tool Scores**
   - Individual score for each tool
   - Helps identify which tool found most issues

3. **Issues by File**
   - File path
   - Line number
   - Column number
   - Severity (error, warning, info)
   - Message (description of issue)
   - Rule ID (for looking up details)

4. **Recommendations**
   - Actionable suggestions from all tools
   - Prioritized by impact

### Example Reports

**Example 1: Passing PR (Score 85)**

```json
{
  "summary": {
    "overall_score": 85.0,
    "tools_run": 3,
    "total_issues": 8,
    "errors": 0,
    "warnings": 8,
    "info": 0
  },
  "tool_scores": {
    "pylint": 88.5,
    "flake8": 84.0,
    "bandit": 82.5
  },
  "issues_by_file": {
    "src/calculator.py": [
      {
        "line": 45,
        "column": 0,
        "severity": "warning",
        "message": "Line too long (105/100)",
        "rule_id": "C0301"
      },
      {
        "line": 67,
        "column": 4,
        "severity": "warning",
        "message": "Missing function docstring",
        "rule_id": "C0116"
      }
    ]
  },
  "recommendations": [
    "Add docstrings to all public functions",
    "Reduce line length to 100 characters or less",
    "Consider adding type hints for better code clarity"
  ]
}
```

**Interpretation:**
- ✅ **APPROVED** - Score 85 meets threshold (80)
- No errors found (good!)
- 8 warnings (minor style issues)
- All tools scored well (82-88 range)
- Recommendations are suggestions, not blockers

**Example 2: Failing PR (Score 65)**

```json
{
  "summary": {
    "overall_score": 65.0,
    "tools_run": 3,
    "total_issues": 24,
    "errors": 5,
    "warnings": 19,
    "info": 0
  },
  "tool_scores": {
    "pylint": 60.0,
    "flake8": 68.0,
    "bandit": 67.0
  },
  "issues_by_file": {
    "src/main.py": [
      {
        "line": 23,
        "column": 8,
        "severity": "error",
        "message": "Undefined variable 'result'",
        "rule_id": "E0602"
      },
      {
        "line": 45,
        "column": 4,
        "severity": "error",
        "message": "SQL query constructed with string formatting (SQL injection risk)",
        "rule_id": "B608"
      }
    ]
  },
  "recommendations": [
    "Fix undefined variable 'result' at line 23",
    "Use parameterized queries to prevent SQL injection",
    "Add error handling for database operations",
    "Reduce function complexity (too many branches)"
  ]
}
```

**Interpretation:**
- ❌ **BLOCKED** - Score 65 below threshold (80)
- 5 errors found (CRITICAL - must fix)
- Error at line 23: undefined variable (bug)
- Error at line 45: SQL injection risk (security issue)
- Must address errors before resubmitting

### Acting on Feedback

**Priority Levels:**

1. **🔴 Errors (Blocking)** - Must fix before approval
   - Undefined variables
   - Import errors
   - Security vulnerabilities (high severity)
   - Syntax errors

2. **⚠️ Warnings (Suggestions)** - Should address but not blocking
   - Style violations
   - Missing docstrings
   - Complexity warnings
   - Minor security issues (low severity)

3. **ℹ️ Info (Optional)** - Nice to have improvements
   - Convention suggestions
   - Best practice recommendations

**Workflow:**

1. **Review PR feedback** - Check blocking issues list
2. **Fix errors first** - Address all 🔴 error-level issues
3. **Resubmit PR** - Push fixes and re-trigger review
4. **Iterate if needed** - Up to 3 feedback cycles
5. **Address warnings** - Improve code quality (optional but recommended)

---

## Advanced Configuration

### Combining Tool Configurations

Use both Moderator config AND tool-specific configs:

```yaml
# config/config.yaml (Moderator config)
gear3:
  qa:
    tools: [pylint, flake8, bandit]
    thresholds:
      error_count: 0
      minimum_score: 80.0
```

```ini
# .pylintrc (tool-specific config)
[MESSAGES CONTROL]
disable = C0111, C0103

[FORMAT]
max-line-length = 100
```

```ini
# .flake8 (tool-specific config)
[flake8]
max-line-length = 100
ignore = E203, W503
```

### Dynamic Thresholds by Branch

Use different configs for different branches:

```yaml
# config/dev_config.yaml (lenient for development)
gear3:
  qa:
    thresholds:
      error_count: 3       # Allow some errors during dev
      minimum_score: 70.0  # Lower bar

# config/prod_config.yaml (strict for production)
gear3:
  qa:
    thresholds:
      error_count: 0       # Zero tolerance
      minimum_score: 90.0  # High bar
```

Usage:

```bash
# Development
python main.py --config config/dev_config.yaml "Feature X"

# Production
python main.py --config config/prod_config.yaml "Feature X"
```

---

## Troubleshooting

### Tool Not Recognized

**Symptom:**
```
WARNING: Unknown QA tool 'pylint' - skipping
```

**Causes:**
1. Tool not installed
2. Tool not in PATH
3. Virtual environment not activated

**Solutions:**

```bash
# Check if tool is installed
which pylint  # Should show path like /usr/local/bin/pylint

# If not found, install
pip install pylint

# If in virtual environment, activate first
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

### Scores Don't Match Expectations

**Symptom:**
Expected score 85, but got 65.

**Debugging:**

```bash
# Check per-tool scores in logs
tail -f state/proj_*/logs.jsonl | grep tool_scores

# Example output:
# "tool_scores": {"pylint": 60.0, "flake8": 85.0, "bandit": 50.0}
```

**Analysis:**

Low bandit score (50.0) is dragging down overall average.

**Solution:**

Either fix security issues OR adjust weights:

```yaml
gear3:
  qa:
    tool_weights:
      bandit: 0.5   # Reduce bandit impact
```

### Too Many False Positives

**Symptom:**
Bandit reports false positives for legitimate code patterns.

**Solution:**

Add inline comments to suppress specific findings:

```python
# Suppress bandit warning for this line only
password = get_password_from_env()  # nosec B105

# Or suppress entire function
def authenticate():  # nosec
    password = config['password']
    # ...
```

Or update `.bandit` config to skip tests globally:

```yaml
# .bandit
skips:
  - B105  # hardcoded_password_string
```

### Configuration Not Taking Effect

**Symptom:**
Changed `config.yaml` but QA still uses old settings.

**Checklist:**

1. **Verify file path:**
   ```bash
   # Check which config is being used
   python main.py --config config/config.yaml "test"
   ```

2. **Verify YAML syntax:**
   ```bash
   # Parse config file to check for errors
   python -c "import yaml; print(yaml.safe_load(open('config/config.yaml')))"
   ```

3. **Check indentation:**
   ```yaml
   # CORRECT:
   gear3:
     qa:
       tools: [pylint]

   # INCORRECT (wrong indentation):
   gear3:
   qa:
     tools: [pylint]
   ```

4. **Restart Moderator:**
   Configuration is loaded at startup, not dynamically.

---

## Configuration Validation

Moderator validates the `gear3.qa` configuration section at startup to catch errors early. This section documents valid patterns, common mistakes, and error messages.

### Valid Configuration Patterns

**Minimal Valid Configuration:**

```yaml
gear3:
  qa:
    tools: []  # Empty list (QA disabled)
```

**Complete Valid Configuration:**

```yaml
gear3:
  qa:
    tools: [pylint, flake8, bandit]
    thresholds:
      error_count: 0
      warning_count: 10
      minimum_score: 80.0
    fail_on_error: true
    tool_weights:
      pylint: 1.0
      flake8: 1.0
      bandit: 1.0
```

**Partially Specified (Uses Defaults):**

```yaml
gear3:
  qa:
    tools: [pylint]
    # thresholds, fail_on_error, tool_weights use defaults
```

### Configuration Validator Behavior

**Validation Timing:**
- Configuration is validated when Moderator starts
- Invalid configuration causes immediate failure with error message
- Validation is **fail-fast** - stops on first error

**What is Validated:**

1. **Type Checking:**
   - `tools` must be a list
   - `thresholds` must be a dict
   - `fail_on_error` must be a boolean
   - Threshold values must be integers

2. **Value Validation:**
   - Tools must be one of: `pylint`, `flake8`, `bandit`
   - Threshold values must be ≥ 0
   - Tool weights must be numeric (int or float)

3. **Structure Validation:**
   - `gear3` section is optional (missing = Gear 2 mode)
   - `qa` subsection is optional (missing = QA disabled)
   - All fields within `qa` are optional (use defaults)

**Backward Compatibility:**

The validator ensures 100% backward compatibility:
- Missing `gear3` section → No validation, runs in Gear 2 mode
- Missing `qa` subsection → No QA validation, QA disabled
- Only validates structure if `gear3.qa` exists

### Common Configuration Mistakes

#### Mistake 1: Invalid Tool Name

**Configuration:**

```yaml
gear3:
  qa:
    tools: [pylint, flake, bandit]  # ❌ 'flake' should be 'flake8'
```

**Error Message:**

```
Configuration error at 'gear3.qa.tools': Invalid QA tool: 'flake'
  Expected: One of: pylint, flake8, bandit
  Actual: flake
```

**Fix:**

```yaml
gear3:
  qa:
    tools: [pylint, flake8, bandit]  # ✅ Correct spelling
```

#### Mistake 2: Wrong Type for tools

**Configuration:**

```yaml
gear3:
  qa:
    tools: pylint  # ❌ Should be a list, not a string
```

**Error Message:**

```
Configuration error at 'gear3.qa.tools': Must be a list
  Expected: list of QA tool names
  Actual: str
```

**Fix:**

```yaml
gear3:
  qa:
    tools: [pylint]  # ✅ Wrap in list brackets
```

#### Mistake 3: Negative Threshold Value

**Configuration:**

```yaml
gear3:
  qa:
    thresholds:
      error_count: -1  # ❌ Negative values not allowed
```

**Error Message:**

```
Configuration error at 'gear3.qa.thresholds.error_count': Threshold must be non-negative
  Expected: >= 0
  Actual: -1
```

**Fix:**

```yaml
gear3:
  qa:
    thresholds:
      error_count: 0  # ✅ Use 0 or positive integer
```

#### Mistake 4: Wrong Type for fail_on_error

**Configuration:**

```yaml
gear3:
  qa:
    fail_on_error: "true"  # ❌ String instead of boolean
```

**Error Message:**

```
Configuration error at 'gear3.qa.fail_on_error': Must be a boolean value
  Expected: true or false
  Actual: str
```

**Fix:**

```yaml
gear3:
  qa:
    fail_on_error: true  # ✅ Boolean without quotes
```

#### Mistake 5: Wrong Type for Thresholds

**Configuration:**

```yaml
gear3:
  qa:
    thresholds: 5  # ❌ Should be dict, not integer
```

**Error Message:**

```
Configuration error at 'gear3.qa.thresholds': Must be a dictionary
  Expected: dict with error/warning keys
  Actual: int
```

**Fix:**

```yaml
gear3:
  qa:
    thresholds:
      error_count: 5
      warning_count: null
```

#### Mistake 6: YAML Indentation Error

**Configuration:**

```yaml
gear3:
qa:  # ❌ Wrong indentation - should be indented under gear3
  tools: [pylint]
```

**Error Message:**

```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Fix:**

```yaml
gear3:
  qa:  # ✅ Properly indented with 2 spaces
    tools: [pylint]
```

#### Mistake 7: Threshold as String Instead of Int

**Configuration:**

```yaml
gear3:
  qa:
    thresholds:
      error_count: "5"  # ❌ String instead of integer
```

**Error Message:**

```
Configuration error at 'gear3.qa.thresholds.error_count': Threshold must be an integer
  Expected: integer
  Actual: str
```

**Fix:**

```yaml
gear3:
  qa:
    thresholds:
      error_count: 5  # ✅ Remove quotes for integer
```

#### Mistake 8: Using minimum_score in Thresholds

**Configuration:**

```yaml
gear3:
  qa:
    thresholds:
      error_count: 0
      minimum_score: 80.0  # ⚠️ Valid in config but not used in config_validator
```

**Note:** The `config_validator.py` currently only validates `error` and `warning` keys in thresholds dict. The `minimum_score` is validated by QAManager at runtime, not at config load time. This is **valid** configuration but not caught by early validation.

**Best Practice:** Use standard threshold names that are validated:

```yaml
gear3:
  qa:
    thresholds:
      error_count: 0
      warning_count: null
      minimum_score: 80.0  # Handled by QAManager
```

### Testing Configuration Validation

**Manual Testing:**

```bash
# Test configuration syntax
python -c "import yaml; print(yaml.safe_load(open('config/config.yaml')))"

# If successful, prints parsed config
# If syntax error, shows YAML error message
```

**Automated Validation:**

```python
from pathlib import Path
from src.config_validator import validate_config
import yaml

# Load and validate config
config_path = Path("config/config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

try:
    validate_config(config)
    print("✅ Configuration is valid")
except Exception as e:
    print(f"❌ Configuration error: {e}")
```

### Valid Configuration Templates

**Template 1: Minimal QA (Pylint Only)**

```yaml
gear3:
  qa:
    tools: [pylint]
    thresholds:
      error_count: 0
      warning_count: null
      minimum_score: 70.0
```

**Validation:** ✅ PASS
- tools: valid list with valid tool name
- thresholds: valid dict with valid integer values
- All types correct

**Template 2: All Tools with Custom Weights**

```yaml
gear3:
  qa:
    tools: [pylint, flake8, bandit]
    thresholds:
      error_count: 0
      warning_count: 10
      minimum_score: 80.0
    fail_on_error: true
    tool_weights:
      pylint: 1.0
      flake8: 1.0
      bandit: 2.0
```

**Validation:** ✅ PASS
- All fields present with correct types
- Tool names valid
- Thresholds non-negative integers
- fail_on_error is boolean
- tool_weights are numeric

**Template 3: QA Disabled**

```yaml
gear3:
  qa:
    tools: []
```

**Validation:** ✅ PASS
- Empty tools list is valid (QA disabled)
- No other fields required

**Template 4: Missing gear3 Section**

```yaml
# No gear3 section at all
project:
  name: "my-project"
backend:
  type: "claude_code"
```

**Validation:** ✅ PASS
- Missing gear3 section is valid (Gear 2 mode)
- No QA validation performed

---

## Additional Resources

- [Pylint Documentation](https://pylint.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Configuration Reference](../config/config.yaml)
- [QAManager Source](../src/qa/qa_manager.py)

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [README.md QA Integration](../README.md#gear-3-quality-assurance-integration)
3. Open an issue on GitHub repository

---

*Last updated: November 2024*
