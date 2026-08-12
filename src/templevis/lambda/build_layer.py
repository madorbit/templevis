"""
Build script for creating AWS Lambda layer with TempleVis dependencies

This script:
1. Creates a virtual environment
2. Installs dependencies from requirements.txt
3. Packages them into Lambda layer format
4. Creates a ZIP file ready for upload

Usage:
    python3 build_layer.py [--output-dir OUTPUT_DIR] [--python-version 3.11]

Output:
    templevis-layer.zip - Ready to upload to S3 or deploy to Lambda
"""

import os
import sys
import shutil
import subprocess
import argparse
import zipfile
from pathlib import Path

# Configuration
DEFAULT_PYTHON_VERSION = "3.11"
DEFAULT_OUTPUT_DIR = "build"


def setup_parser():
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Build AWS Lambda layer for TempleVis"
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for layer (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--python-version",
        default=DEFAULT_PYTHON_VERSION,
        help=f"Python version for layer (default: {DEFAULT_PYTHON_VERSION})"
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary build directory"
    )
    return parser


def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return output"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    
    if result.returncode != 0 and check:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    
    return result


def create_layer_structure(base_dir, python_version):
    """Create Lambda layer directory structure"""
    layer_dir = Path(base_dir) / "layer"
    python_libs = layer_dir / f"python/lib/python{python_version}/site-packages"
    
    python_libs.mkdir(parents=True, exist_ok=True)
    return layer_dir, python_libs


def install_requirements(python_libs, requirements_file):
    """Install Python dependencies for Lambda"""
    print(f"Installing requirements from {requirements_file}...")
    
    # For Lambda, we need to use manylinux binaries
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--platform",
        "manylinux2014_x86_64",
        "--target",
        str(python_libs),
        "--python-version",
        "311",
        "--only-binary=:all:",
        "--upgrade",
        "-r",
        requirements_file
    ]
    
    result = run_command(cmd, check=False)
    
    if result.returncode != 0:
        # Try without platform restrictions (for testing locally)
        print("Warning: manylinux build failed, attempting standard install")
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--target",
            str(python_libs),
            "--upgrade",
            "-r",
            requirements_file
        ]
        run_command(cmd)


def install_templevis(python_libs, project_root):
    """Install TempleVis package into layer"""
    print(f"Installing TempleVis package...")
    
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--target",
        str(python_libs),
        "--upgrade",
        project_root
    ]
    
    run_command(cmd, check=False)


def create_layer_zip(layer_dir, output_file):
    """Create ZIP file from layer directory"""
    print(f"Creating layer archive: {output_file}")
    
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(layer_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, layer_dir)
                zipf.write(file_path, arcname)
    
    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"Layer created: {output_file} ({size_mb:.2f} MB)")


def cleanup(base_dir, keep_temp):
    """Clean up temporary directories"""
    if not keep_temp:
        print("Cleaning up temporary files...")
        shutil.rmtree(base_dir, ignore_errors=True)
    else:
        print(f"Temporary files kept in: {base_dir}")


def main():
    parser = setup_parser()
    args = parser.parse_args()
    
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    requirements_file = project_root / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"Error: requirements.txt not found at {requirements_file}")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_zip = output_dir / "templevis-layer.zip"
    
    try:
        # Create layer structure
        layer_dir, python_libs = create_layer_structure(output_dir, args.python_version)
        
        # Install dependencies
        install_requirements(python_libs, str(requirements_file))
        
        # Install TempleVis
        install_templevis(python_libs, str(project_root))
        
        # Create ZIP archive
        create_layer_zip(layer_dir, str(output_zip))
        
        print()
        print("=" * 60)
        print("Lambda layer built successfully!")
        print("=" * 60)
        print(f"Output file: {output_zip}")
        print()
        print("Upload to AWS:")
        print(f"  aws s3 cp {output_zip} s3://your-bucket/templevis-layer.zip")
        print()
        print("Or deploy with CloudFormation/Terraform")
        print()
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        cleanup(output_dir, args.keep_temp)
        return 1
    
    finally:
        if not args.keep_temp:
            cleanup(output_dir, args.keep_temp)


if __name__ == "__main__":
    sys.exit(main())
