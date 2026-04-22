"""
Setup script for CrossFlow AI Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="crossflow-sdk",
    version="1.0.0",
    author="CrossFlow AI Team",
    author_email="sdk@crossflow.ai",
    description="Python SDK for CrossFlow AI Trading Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/crossflow-ai/python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
        "websockets>=11.0.0",
        "pydantic>=2.0.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="crossflow defi cross-chain trading intent-based sdk",
    project_urls={
        "Bug Reports": "https://github.com/crossflow-ai/python-sdk/issues",
        "Source": "https://github.com/crossflow-ai/python-sdk",
        "Documentation": "https://docs.crossflow.ai/sdk/python",
    },
)