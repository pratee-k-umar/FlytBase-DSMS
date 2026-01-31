#!/usr/bin/env python3
"""
DSMS Unified Development Server
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


# Colors for output
class Colors:
    CYAN = "\033[0;36m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    RED = "\033[0;31m"
    NC = "\033[0m"  # No Color


def print_colored(message, color):
    print(f"{color}{message}{Colors.NC}")


def check_python_dependencies():
    """Check and install Python dependencies if needed"""
    print_colored("Checking Python dependencies...", Colors.CYAN)

    # Find virtual environment Python
    venv_python = os.path.join("src", "dsms", "venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = os.path.join("src", "dsms", ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable  # Fallback to system Python

    requirements_file = os.path.join("src", "dsms", "requirements.txt")

    try:
        result = subprocess.run(
            [
                venv_python,
                "-c",
                'import django, mongoengine, channels, rest_framework, celery; print("OK")',
            ],
            capture_output=True,
            text=True,
            cwd=os.path.join("src", "dsms"),
        )

        if result.returncode == 0:
            print_colored("[OK] Python dependencies are up to date", Colors.GREEN)
            return True
        else:
            print_colored("[INFO] Installing Python dependencies...", Colors.YELLOW)

            # Install dependencies
            install_result = subprocess.run(
                [venv_python, "-m", "pip", "install", "-r", requirements_file],
                capture_output=False,
                text=True,
            )

            if install_result.returncode == 0:
                print_colored(
                    "[OK] Python dependencies installed successfully", Colors.GREEN
                )
                return True
            else:
                print_colored(
                    "[ERROR] Failed to install Python dependencies", Colors.RED
                )
                return False

    except Exception as e:
        print_colored(f"[ERROR] Error with Python dependencies: {e}", Colors.RED)
        return False


def check_mongodb():
    """Check if MongoDB is running"""
    print_colored("Checking MongoDB connection...", Colors.CYAN)

    # If using cloud MongoDB, skip local check
    if "MONGODB_URI" in os.environ:
        print_colored("[OK] Using cloud MongoDB (MONGODB_URI is set)", Colors.GREEN)
        return True

    try:
        import pymongo
        from pymongo import MongoClient

        # Check local MongoDB
        mongodb_uri = "mongodb://localhost:27017/"

        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print_colored("[OK] MongoDB is running", Colors.GREEN)
        return True
    except Exception as e:
        print_colored(f"[WARNING] Local MongoDB not found: {e}", Colors.YELLOW)
        print_colored(
            "[TIP] Set MONGODB_URI environment variable for cloud MongoDB or start local MongoDB",
            Colors.YELLOW,
        )
        return False


def check_redis():
    """Check if Redis is running"""
    print_colored("Checking Redis connection...", Colors.CYAN)

    # If using cloud Redis, skip local check
    if "REDIS_URL" in os.environ:
        print_colored("[OK] Using cloud Redis (REDIS_URL is set)", Colors.GREEN)
        return True

    try:
        import redis

        # Check local Redis
        r = redis.Redis(host="localhost", port=6379, db=0, socket_timeout=5)
        r.ping()
        print_colored("[OK] Redis is running", Colors.GREEN)
        return True
    except Exception as e:
        print_colored(f"[WARNING] Local Redis not found: {e}", Colors.YELLOW)
        print_colored(
            "[TIP] Set REDIS_URL environment variable for cloud Redis or start local Redis",
            Colors.YELLOW,
        )
        return False


def check_frontend_dependencies():
    """Check and install frontend dependencies if needed"""
    print_colored("Checking frontend dependencies...", Colors.CYAN)

    node_modules = Path("node_modules")
    package_json = Path("package.json")

    if not package_json.exists():
        print_colored("[ERROR] package.json not found", Colors.RED)
        return False

    needs_install = False

    if not node_modules.exists() or not any(node_modules.iterdir()):
        print_colored("[INFO] Frontend dependencies not installed", Colors.YELLOW)
        needs_install = True
    else:
        # Check if package-lock.json is newer than node_modules (dependencies changed)
        package_lock = Path("package-lock.json")
        if package_lock.exists():
            if package_lock.stat().st_mtime > node_modules.stat().st_mtime:
                print_colored(
                    "[INFO] Dependencies updated, reinstalling...", Colors.YELLOW
                )
                needs_install = True

    if needs_install:
        print_colored("Installing frontend dependencies...", Colors.CYAN)
        try:
            npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
            result = subprocess.run(
                [npm_cmd, "install"],
                shell=True,
                capture_output=False,
                text=True,
            )
            if result.returncode == 0:
                print_colored(
                    "[OK] Frontend dependencies installed successfully", Colors.GREEN
                )
                return True
            else:
                print_colored(
                    "[ERROR] Failed to install frontend dependencies", Colors.RED
                )
                return False
        except Exception as e:
            print_colored(
                f"[ERROR] Failed to install frontend dependencies: {e}", Colors.RED
            )
            return False

    print_colored("[OK] Frontend dependencies are up to date", Colors.GREEN)
    return True


def start_django_server():
    """Start Django development server"""
    print_colored("Starting Django server...", Colors.GREEN)

    # Use virtual environment
    venv_python = os.path.join("src", "dsms", "venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = os.path.join("src", "dsms", ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable  # Fallback to system Python

    # manage.py is now at root
    return subprocess.Popen([venv_python, "manage.py", "runserver", "0.0.0.0:8000"])


def start_webpack_dev_server():
    """Start Webpack dev server for frontend"""
    print_colored("Starting Webpack dev server...", Colors.GREEN)

    try:
        # On Windows, use npm.cmd, on Unix use npm
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        return subprocess.Popen([npm_cmd, "run", "dev:frontend"], shell=True)
    except FileNotFoundError:
        print_colored(
            "[WARNING] npm not found. Install Node.js to run frontend.", Colors.YELLOW
        )
        return None


def main():
    parser = argparse.ArgumentParser(description="DSMS Unified Development Server")
    parser.add_argument(
        "--skip-checks", action="store_true", help="Skip dependency checks"
    )
    parser.add_argument(
        "--django-only", action="store_true", help="Run Django only (backend)"
    )
    parser.add_argument(
        "--frontend-only", action="store_true", help="Run frontend only"
    )

    args = parser.parse_args()

    print_colored("DSMS Django Development Server", Colors.CYAN)
    print_colored("==============================", Colors.CYAN)

    # Change to project root
    os.chdir(Path(__file__).parent)

    # Check dependencies unless skipped
    if not args.skip_checks:
        checks_passed = True
        frontend_checks_passed = True

        # Backend checks
        checks_passed &= check_python_dependencies()

        # Frontend checks (only if not running django-only)
        if not args.django_only:
            frontend_checks_passed = check_frontend_dependencies()

        # MongoDB and Redis checks are now warnings only for cloud setups
        mongodb_ok = check_mongodb()
        redis_ok = check_redis()

        # Exit if dependencies failed to install
        if not checks_passed:
            print_colored(
                "\n[ERROR] Failed to setup Python dependencies",
                Colors.RED,
            )
            sys.exit(1)

        if not args.django_only and not frontend_checks_passed:
            print_colored(
                "\n[ERROR] Failed to setup frontend dependencies",
                Colors.RED,
            )
            sys.exit(1)

        # Warn but don't fail for MongoDB/Redis
        if not mongodb_ok or not redis_ok:
            print_colored(
                "\n[WARNING] Some services are not running locally. Make sure environment variables are set.",
                Colors.YELLOW,
            )
            print_colored("   Continuing anyway...\n", Colors.YELLOW)

    # Start servers based on flags
    processes = []

    try:
        if args.frontend_only:
            # Start only Webpack dev server
            print_colored("\nStarting Webpack dev server...", Colors.CYAN)
            webpack_process = start_webpack_dev_server()
            if webpack_process:
                processes.append(("Webpack", webpack_process))

                print_colored("\nDSMS Frontend is running!", Colors.GREEN)
                print_colored("==========================", Colors.GREEN)
                print_colored("Frontend: http://localhost:3000", Colors.GREEN)
                print_colored("\nPress Ctrl+C to stop the server", Colors.YELLOW)
            else:
                print_colored(
                    "\n[ERROR] Failed to start Webpack dev server", Colors.RED
                )
                sys.exit(1)
        elif args.django_only:
            # Start only Django server
            print_colored("\nStarting Django server...", Colors.CYAN)
            django_process = start_django_server()
            if django_process:
                processes.append(("Django", django_process))

                print_colored("\nDSMS Django API is running!", Colors.GREEN)
                print_colored("============================", Colors.GREEN)
                print_colored("Django API: http://localhost:8000", Colors.GREEN)
                print_colored("API Docs: http://localhost:8000/api/", Colors.GREEN)
                print_colored(
                    "Health Check: http://localhost:8000/health/", Colors.GREEN
                )
                print_colored("\nPress Ctrl+C to stop the server", Colors.YELLOW)
            else:
                print_colored("\n[ERROR] Failed to start Django server", Colors.RED)
                sys.exit(1)
        else:
            # Start both Django and Webpack dev servers
            print_colored("\nStarting Django server...", Colors.CYAN)
            django_process = start_django_server()
            if django_process:
                processes.append(("Django", django_process))
            else:
                print_colored("\n[ERROR] Failed to start Django server", Colors.RED)
                sys.exit(1)

            print_colored("Starting Webpack dev server...", Colors.CYAN)
            webpack_process = start_webpack_dev_server()
            if webpack_process:
                processes.append(("Webpack", webpack_process))
            else:
                print_colored(
                    "\n[ERROR] Failed to start Webpack dev server", Colors.RED
                )
                # Cleanup already started processes
                for name, process in processes:
                    print_colored(f"Stopping {name}...", Colors.YELLOW)
                    if process:
                        process.terminate()
                        process.wait()
                sys.exit(1)

            print_colored("\nDSMS is running!", Colors.GREEN)
            print_colored("=================", Colors.GREEN)
            print_colored("Django API: http://localhost:8000", Colors.GREEN)
            print_colored("Frontend: http://localhost:3000", Colors.GREEN)
            print_colored("API Docs: http://localhost:8000/api/", Colors.GREEN)
            print_colored("Health Check: http://localhost:8000/health/", Colors.GREEN)
            print_colored("\nPress Ctrl+C to stop all servers", Colors.YELLOW)

        # Wait for processes
        for name, process in processes:
            if process:
                process.wait()

    except KeyboardInterrupt:
        print_colored("\nStopping servers...", Colors.YELLOW)

        for name, process in processes:
            if process:
                print_colored(f"Stopping {name}...", Colors.YELLOW)
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    # Force kill if terminate doesn't work
                    try:
                        process.kill()
                    except Exception:
                        pass

        print_colored("[OK] Servers stopped", Colors.GREEN)

    except Exception as e:
        print_colored(f"[ERROR] Error: {e}", Colors.RED)
        # Cleanup processes
        for name, process in processes:
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    pass
        sys.exit(1)


if __name__ == "__main__":
    main()
