#!/usr/bin/env python3
"""Development runner for Art Factory.

This script handles virtual environment activation and application startup
for development purposes.
"""

import sys
import os
import subprocess
from pathlib import Path

# Get project root directory
project_root = Path(__file__).parent.parent
app_dir = project_root / "app"
venv_dir = project_root / "venv"

def check_virtual_environment():
    """Check if virtual environment exists and is activated."""
    if not venv_dir.exists():
        print("❌ Virtual environment not found!")
        print(f"Expected location: {venv_dir}")
        print("Run: python3 -m venv venv")
        return False

    # Check if we're in the virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return True

    # Not in virtual environment, try to activate and run
    return False

def run_in_venv():
    """Run the application in the virtual environment."""
    if os.name == 'nt':  # Windows
        python_exe = venv_dir / "Scripts" / "python.exe"
        activate_script = venv_dir / "Scripts" / "activate.bat"
    else:  # macOS/Linux
        python_exe = venv_dir / "bin" / "python"
        activate_script = venv_dir / "bin" / "activate"

    if not python_exe.exists():
        print(f"❌ Python executable not found: {python_exe}")
        return 1

    # Build command to run main.py
    cmd = [str(python_exe), str(app_dir / "main.py")] + sys.argv[1:]

    print(f"🚀 Starting Art Factory...")
    if "--debug" in sys.argv:
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Virtual env: {venv_dir}")

    try:
        return subprocess.run(cmd, cwd=project_root).returncode
    except KeyboardInterrupt:
        print("\\n👋 Art Factory stopped")
        return 0
    except Exception as e:
        print(f"❌ Error running application: {e}")
        return 1

def main():
    """Main entry point."""
    print("Art Factory Development Runner")
    print("=" * 40)

    # Check if we're already in virtual environment
    if check_virtual_environment():
        # Already in venv, run directly
        sys.path.insert(0, str(app_dir))
        from main import main as app_main
        return app_main()
    else:
        # Not in venv, run through venv
        return run_in_venv()

if __name__ == "__main__":
    sys.exit(main())