from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentic-analytics",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A multi-agent data analyst chatbot using LangGraph and Streamlit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hollylessthan/AgenticAnalytics",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "streamlit>=1.30.0",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "langgraph>=0.0.20",
        "faiss-cpu>=1.7.4",
        "sqlalchemy>=2.0.0",
        "pandas>=2.1.0",
        "matplotlib>=3.8.0",
        "plotly>=5.18.0",
    ],
)
