# Environment Setup Guide

Complete guide for setting up your Python environment for Agentic Analytics.

## Table of Contents

- [Python Version Requirements](#python-version-requirements)
- [Virtual Environment Setup](#virtual-environment-setup)
- [Dependency Installation](#dependency-installation)
- [Troubleshooting](#troubleshooting)
- [IDE Configuration](#ide-configuration)

---

## Python Version Requirements

**Required:** Python 3.9 or higher  
**Recommended:** Python 3.12 (latest stable)

### Check Your Python Version

```bash
python --version
# or
python3 --version
```

### Installing Python 3.12

#### macOS

**Option 1: Direct Download (Recommended)**
1. Visit https://www.python.org/downloads/
2. Download Python 3.12.x macOS installer
3. Install the .pkg file
4. Verify: `python3.12 --version`

**Option 2: Using Homebrew**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12
brew install python@3.12

# Verify
python3.12 --version
```

#### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python 3.12
sudo apt install python3.12 python3.12-venv python3.12-dev

# Verify
python3.12 --version
```

#### Windows

1. Visit https://www.python.org/downloads/
2. Download Python 3.12.x Windows installer
3. **Important:** Check "Add Python to PATH" during installation
4. Verify: `python --version`

---

## Virtual Environment Setup

### Why Use a Virtual Environment?

✅ **Isolation** - Dependencies don't conflict with other projects  
✅ **Reproducibility** - Same environment on all machines  
✅ **Clean** - Easy to delete and recreate  
✅ **Best Practice** - Industry standard for Python projects

### Creating a Virtual Environment

#### Method 1: Using venv (Built-in, Recommended)

```bash
# Navigate to project directory
cd AgenticAnalytics

# Create virtual environment named .venv
python3.12 -m venv .venv

# Or use default python if it's 3.9+
python -m venv .venv
```

**Why `.venv`?**
- Hidden folder (starts with `.`)
- Standard naming convention
- Auto-detected by VS Code
- Already in `.gitignore`

#### Method 2: Using Conda/Miniconda

```bash
# Create environment with Python 3.12
conda create -n agentic-analytics python=3.12

# Alternative: create from environment file
conda env create -f environment.yml
```

### Activating the Virtual Environment

#### macOS / Linux

```bash
# Activate
source .venv/bin/activate

# You should see (.venv) in your prompt:
# (.venv) user@machine:~/AgenticAnalytics$
```

#### Windows (Command Prompt)

```cmd
.venv\Scripts\activate.bat
```

#### Windows (PowerShell)

```powershell
.venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Verifying Activation

```bash
# Check Python location (should point to .venv)
which python  # macOS/Linux
where python  # Windows

# Should show: /path/to/AgenticAnalytics/.venv/bin/python

# Check version
python --version
```

### Deactivating

```bash
deactivate
```

---

## Dependency Installation

### Install All Dependencies

```bash
# Make sure virtual environment is activated
# You should see (.venv) in your prompt

# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This will install ~50 packages (takes 2-3 minutes)
```

### Verify Installation

```bash
# Check installed packages
pip list

# Test key imports
python -c "import langchain; print('✅ LangChain installed')"
python -c "import pandas; print('✅ Pandas installed')"
python -c "import streamlit; print('✅ Streamlit installed')"
python -c "import duckdb; print('✅ DuckDB installed')"
```

### Optional Dependencies

Some dependencies are commented out in `requirements.txt`. Uncomment based on your needs:

**For Claude (Anthropic):**
```bash
pip install langchain-anthropic
```

**For Gemini (Google):**
```bash
pip install langchain-google-genai
```

**For AWS Bedrock:**
```bash
pip install langchain-aws boto3
```

**For Weaviate vector store:**
```bash
pip install weaviate-client
```

**For local embeddings:**
```bash
pip install langchain-huggingface sentence-transformers
```

### Installation for Development

If you're contributing or developing:

```bash
# Install with development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists

# Or install common dev tools
pip install pytest black flake8 mypy
```

---

## Troubleshooting

### "command not found: python"

**Solution:** Use `python3` instead:
```bash
python3 -m venv .venv
```

### "No module named 'venv'"

**Solution:** Install python3-venv:
```bash
# Ubuntu/Debian
sudo apt install python3.12-venv

# Or use virtualenv
pip install virtualenv
virtualenv .venv
```

### Permission Denied on Windows PowerShell

**Solution:** Update execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "error: Microsoft Visual C++ 14.0 is required" (Windows)

**Solution:** Install Microsoft C++ Build Tools:
1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++"

### Slow Installation on macOS M1/M2

**Solution:** Some packages need to compile. Install Xcode tools:
```bash
xcode-select --install
```

### ImportError After Installation

**Solution:** Make sure virtual environment is activated:
```bash
# Check
which python

# Should show .venv path
# If not, activate again
source .venv/bin/activate
```

### "pip: command not found"

**Solution:** Use python module syntax:
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Package Conflicts

**Solution:** Clean install:
```bash
# Deactivate
deactivate

# Remove old venv
rm -rf .venv

# Create fresh venv
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## IDE Configuration

### VS Code Setup

#### 1. Select Python Interpreter

1. Open Command Palette: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. Type: "Python: Select Interpreter"
3. Choose: `./.venv/bin/python`

#### 2. Configure Settings

Create/update `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.testing.pytestEnabled": true,
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

#### 3. Install Recommended Extensions

Create `.vscode/extensions.json`:

```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-toolsai.jupyter",
        "charliermarsh.ruff"
    ]
}
```

### PyCharm Setup

1. **Open Project** in PyCharm
2. **File → Settings → Project → Python Interpreter**
3. **Click gear icon → Add**
4. **Select "Existing environment"**
5. **Browse to**: `AgenticAnalytics/.venv/bin/python`
6. **Click OK**

### Jupyter Notebook

```bash
# Install Jupyter in your venv
pip install jupyter ipykernel

# Create kernel
python -m ipykernel install --user --name=agentic-analytics

# Launch Jupyter
jupyter notebook
```

---

## Quick Reference

### Daily Workflow

```bash
# 1. Navigate to project
cd AgenticAnalytics

# 2. Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# 3. Work on your code
# ...

# 4. Install new package (if needed)
pip install package-name

# 5. Update requirements (if you added packages)
pip freeze > requirements.txt

# 6. Deactivate when done
deactivate
```

### Common Commands

```bash
# Check Python version
python --version

# Check where Python is running from
which python  # macOS/Linux
where python  # Windows

# List installed packages
pip list

# Show package info
pip show package-name

# Uninstall package
pip uninstall package-name

# Update package
pip install --upgrade package-name

# Install from requirements
pip install -r requirements.txt

# Save current packages
pip freeze > requirements.txt
```

---

## Environment Variables

After setting up your virtual environment, configure environment variables:

```bash
# Copy example file
cp .env.example .env

# Edit with your settings
nano .env  # or use your preferred editor
```

Required variables:
```bash
# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here

# Database Configuration
DATABASE_TYPE=duckdb
DATABASE_PATH=data/analytics.duckdb

# Vector Store Configuration
VECTOR_STORE_TYPE=faiss
EMBEDDING_PROVIDER=openai
```

See [PROVIDERS.md](../PROVIDERS.md) for detailed configuration.

---

## Verification Checklist

Before starting development, verify your setup:

```bash
# ✅ Python version
python --version  # Should be 3.9+

# ✅ Virtual environment activated
which python  # Should show .venv path

# ✅ Dependencies installed
pip list | grep langchain  # Should show LangChain packages

# ✅ Can import key modules
python -c "import langchain, pandas, streamlit, duckdb"

# ✅ Environment variables set
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('✅' if os.getenv('OPENAI_API_KEY') else '❌')"

# ✅ Can run examples
python examples/create_sample_db.py
```

---

## Next Steps

After environment setup:

1. ✅ **Configure Environment** - Edit `.env` file
2. ✅ **Create Sample Database** - `python examples/create_sample_db.py`
3. ✅ **Run Application** - `streamlit run src/app.py`
4. ✅ **Try Examples** - Explore `examples/` directory
5. ✅ **Run Tests** - See [testing/README.md](../testing/README.md)

---

## Getting Help

If you encounter issues:

1. Check [Troubleshooting](#troubleshooting) section above
2. Review [GitHub Issues](https://github.com/hollylessthan/AgenticAnalytics/issues)
3. Check package documentation:
   - [LangChain Docs](https://python.langchain.com/)
   - [Streamlit Docs](https://docs.streamlit.io/)
   - [Python venv Docs](https://docs.python.org/3/library/venv.html)

---

**Successfully set up?** 🎉 You're ready to start using Agentic Analytics!
