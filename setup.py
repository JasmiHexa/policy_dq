"""Setup script for policy-dq package."""

from setuptools import setup, find_packages

setup(
    name="policy-dq",
    version="1.0.0",
    description="Data validation system for structured data files",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "colorama>=0.4.6",
        "click>=8.1.0",
        "chardet>=5.0.0",
        "mcp>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "policy-dq=policy_dq.cli:cli",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.11.0",
            "pytest-cov>=4.1.0",
            "hypothesis>=6.82.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
            "flake8>=6.0.0",
        ]
    },
)