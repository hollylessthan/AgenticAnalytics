"""Setup configuration for Agentic Analytics."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentic-analytics",
    version="0.1.0",
    author="AgenticAnalytics Team",
    description="Multi-agent data analyst chatbot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hollylessthan/AgenticAnalytics",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.29.0",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "langgraph>=0.0.20",
        "openai>=1.6.0",
        "weaviate-client>=4.0.0",
        "faiss-cpu>=1.7.4",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "sqlalchemy>=2.0.0",
        "plotly>=5.18.0",
        "matplotlib>=3.8.0",
        "seaborn>=0.13.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
    ],
)
