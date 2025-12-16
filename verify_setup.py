#!/usr/bin/env python
"""Verify installation and configuration of Agentic Analytics."""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro}")
        print("   Required: Python 3.9 or higher")
        return False


def check_dependencies():
    """Check if required packages are installed."""
    print("\n📦 Checking dependencies...")
    required = [
        "streamlit",
        "langchain",
        "langchain_openai",
        "langgraph",
        "faiss",
        "sqlalchemy",
        "pandas",
        "matplotlib",
        "plotly",
        "python-dotenv"
    ]
    
    missing = []
    for package in required:
        try:
            if package == "faiss":
                __import__("faiss")
            elif package == "python-dotenv":
                __import__("dotenv")
            else:
                __import__(package.replace("-", "_"))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n   Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    return True


def check_env_file():
    """Check if .env file exists and has required variables."""
    print("\n⚙️  Checking configuration...")
    env_path = Path(".env")
    
    if not env_path.exists():
        print("   ❌ .env file not found")
        print("   Run: cp .env.example .env")
        return False
    
    print("   ✅ .env file exists")
    
    # Check for required variables
    required_vars = ["OPENAI_API_KEY", "DATABASE_URL"]
    with open(env_path) as f:
        content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in content or f"{var}=your_" in content or f"{var}=\n" in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"   ⚠️  Configure these variables: {', '.join(missing_vars)}")
        return False
    
    print("   ✅ Required variables configured")
    return True


def check_directories():
    """Check if required directories exist."""
    print("\n📁 Checking directories...")
    required_dirs = [
        "src",
        "src/agents",
        "src/rag",
        "src/utils",
        "examples",
        "tests",
        "data",
        "outputs/visualizations"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} - MISSING")
            all_exist = False
    
    return all_exist


def check_database():
    """Check if database is accessible."""
    print("\n🗄️  Checking database...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from src.utils.database import DatabaseManager
        db = DatabaseManager()
        tables = db.get_tables()
        
        if tables:
            print(f"   ✅ Database connected ({len(tables)} tables found)")
            print(f"   Tables: {', '.join(tables[:5])}")
            return True
        else:
            print("   ⚠️  Database connected but no tables found")
            print("   Run: python examples/create_sample_db.py")
            return False
            
    except Exception as e:
        print(f"   ❌ Database error: {str(e)}")
        print("   Check your DATABASE_URL in .env")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("Agentic Analytics - Installation Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration", check_env_file),
        ("Directories", check_directories),
        ("Database", check_database)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n   ❌ Error during {name} check: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All checks passed! You're ready to go!")
        print("\nNext steps:")
        print("  1. streamlit run src/app.py")
        print("  2. Click 'Initialize Systems' in sidebar")
        print("  3. Ask your first question!")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - pip install -r requirements.txt")
        print("  - cp .env.example .env (then edit .env)")
        print("  - python examples/create_sample_db.py")
    
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
