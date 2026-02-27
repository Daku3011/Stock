#!/usr/bin/env python3
"""
Universal Start Script for Stock Dashboard
Detects OS and runs appropriate commands
"""

import sys
import os
import subprocess
import platform

def get_os():
    """Detect operating system"""
    return platform.system()

def run_windows():
    """Run on Windows"""
    print("🪟 Windows detected")
    subprocess.run(["cmd.exe", "/c", "run.bat"])

def run_unix():
    """Run on Linux/macOS"""
    os_name = get_os()
    print(f"🐧 {os_name} detected")
    subprocess.run(["bash", "run.sh"])

def main():
    print("\n" + "="*60)
    print("🤖 Stock Analysis Dashboard")
    print("="*60 + "\n")
    
    os_type = get_os()
    
    if os_type == "Windows":
        run_windows()
    elif os_type in ["Linux", "Darwin"]:
        run_unix()
    else:
        print(f"⚠️ Unknown OS: {os_type}")
        print("Attempting to run app.py directly...")
        subprocess.run([sys.executable, "app.py"])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
