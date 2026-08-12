"""
TempleVis - Temple Worker Schedule Visualization Tool

A tool for processing LDS temple worker schedule PDFs and generating CSV reports
of task assignments and time periods.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    try:
        long_description = fh.read()
    except FileNotFoundError:
        long_description = "README.md not found. Please refer to project documentation."

setup(
    name="templevis",
    version="0.1.0",
    author="Temple Technology Team",
    author_email="temple.tech@example.com",
    description="A tool for processing temple worker schedule PDFs and generating CSV reports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/templevis",
    project_urls={
        "Bug Tracker": "https://github.com/username/templevis/issues",
        "Documentation": "https://github.com/username/templevis/wiki",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Religion",
        "Topic :: Office/Business :: Scheduling",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        'pandas>=2.1.0',
        'numpy>=1.26.0',
        'pdfplumber>=0.10.2',
        'odfpy>=1.4.1',
        'openpyxl>=3.1.2'
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'templevis=templevis.main:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
