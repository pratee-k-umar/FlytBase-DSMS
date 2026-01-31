#!/usr/bin/env python3
"""
DSMS Setup Validation Script
Validates that the unified development setup is working correctly
"""

import os
import subprocess
import sys
from pathlib import Path


def check_config_files():
    """Check if all config files are in place"""
    required_files = [
        "config/settings/base.py",
        "config/settings/development.py",
        "config/settings/production.py",
        "config/urls.py",
        "next.config.ts",
        "tsconfig.json",
        "package.json",
        "dev.py",
    ]

    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)

    if missing:
        print(f"[ERROR] Missing config files: {', '.join(missing)}")
        return False

    print("[OK] All configuration files are present")
    return True


def check_django_settings():
    """Check if Django can import settings"""
    try:
        # Find virtual environment Python
        venv_python = Path("src/dsms/venv/Scripts/python.exe")
        if not venv_python.exists():
            venv_python = Path("src/dsms/.venv/Scripts/python.exe")
        if not venv_python.exists():
            venv_python = Path(sys.executable)

        # Add project root to path
        project_root = Path(__file__).parent
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        result = subprocess.run(
            [
                str(venv_python),
                "-c",
                'import os; os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dsms.conf.settings.development"); import django; django.setup(); print("OK")',
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
            env=env,
        )

        if result.returncode == 0:
            print("[OK] Django settings loaded successfully")
            return True
        else:
            print(f"[ERROR] Django settings error: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Django settings error: {e}")
        return False


def check_nextjs_config():
    """Check if Next.js config is valid"""
    try:
        result = subprocess.run(
            ["node", "--check", "next.config.ts"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )
        if result.returncode == 0:
            print("[OK] Next.js configuration is valid")
            return True
        else:
            print(f"[ERROR] Next.js config error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("[ERROR] Node.js not found")
        return False


def check_package_json():
    """Check if package.json has unified dev script"""
    try:
        import json

        with open("package.json", "r") as f:
            data = json.load(f)

        if "scripts" in data and "dev" in data["scripts"]:
            if data["scripts"]["dev"] == "python dev.py":
                print("[OK] package.json has unified dev script")
                return True
            else:
                print(f"[ERROR] package.json dev script is: {data['scripts']['dev']}")
                return False
        else:
            print("[ERROR] package.json missing dev script")
            return False
    except Exception as e:
        print(f"[ERROR] Error reading package.json: {e}")
        return False


def main():
    print("DSMS Setup Validation")
    print("=" * 30)

    checks = [
        check_config_files,
        check_django_settings,
        check_nextjs_config,
        check_package_json,
    ]

    passed = 0
    total = len(checks)

    for check in checks:
        if check():
            passed += 1
        print()

    print(f"Results: {passed}/{total} checks passed")

    if passed == total:
        print("[SUCCESS] Setup validation complete! Ready for unified development.")
        print("\nTo start development:")
        print("  make dev")
        print("  npm run dev")
        print("  python dev.py")
        return 0
    else:
        print("[ERROR] Setup validation failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
