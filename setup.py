#!/usr/bin/env python3
"""
Setup Script for Stock Analysis Dashboard
Installs all dependencies and prepares the application
"""

import sys
import os
import subprocess

def check_python_version():
    """Check if Python 3.7+ is installed"""
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        print(f"   Current: Python {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def install_requirements():
    """Install required packages from requirements.txt"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

def verify_installation():
    """Verify that all required packages are installed"""
    print("\n🔍 Verifying installation...")
    required_packages = [
        'yfinance', 'pandas', 'numpy', 'sklearn', 'plotly',
        'requests', 'nltk', 'flask'
    ]
    
    failed = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package}")
            failed.append(package)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        return False
    
    print("\n✅ All dependencies verified!")
    return True

def main():
    print("\n" + "="*60)
    print("🤖 STOCK DASHBOARD - SETUP")
    print("="*60)
    
    # Check Python version
    check_python_version()
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        print("\n⚠️  Some packages may be missing.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print("\n🚀 To start the application, run:")
    print("   python app.py")
    print("\n   Or use the run script:")
    
    if sys.platform == "win32":
        print("   run.bat")
    else:
        print("   ./run.sh")
    
    print("\n📖 Open http://127.0.0.1:5000 in your browser\n")

if __name__ == "__main__":
    main()
