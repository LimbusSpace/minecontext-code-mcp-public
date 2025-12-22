#!/usr/bin/env python3
"""
Setup script to run tests and copy trajectory examples
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def run_test(cmd, test_name):
    """Run a test command and return the trajectory file path"""
    print(f"\n=== Running test: {test_name} ===")
    print(f"Command: {cmd}\n")

    # Run the failure_inspector
    result = subprocess.run(
        ["python", "failure_inspector.py", cmd],
        capture_output=True,
        text=True
    )

    # Print output
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    # Find the latest trajectory file
    trajectories = list(Path(".").glob("trajectory_*.json"))
    if trajectories:
        latest = max(trajectories, key=lambda p: p.stat().st_mtime)
        print(f"\nGenerated: {latest}")
        return latest
    else:
        print("\nNo trajectory file generated!")
        return None

def main():
    base_dir = Path(".")

    # Run tests
    file_not_found_test = run_test("python some_broken_script.py", "File Not Found Error")
    pytest_failure_test = run_test("python -m pytest tests/test_broken.py -v", "Pytest Failure")

    # Create examples directory
    examples_dir = base_dir / "examples"
    examples_dir.mkdir(exist_ok=True)

    # Copy examples
    if file_not_found_test and file_not_found_test.exists():
        target = examples_dir / "trajectory_file_not_found.json"
        shutil.copy(file_not_found_test, target)
        print(f"\n[OK] Copied to: {target}")

    if pytest_failure_test and pytest_failure_test.exists():
        target = examples_dir / "trajectory_pytest_failure.json"
        shutil.copy(pytest_failure_test, target)
        print(f"✓ Copied to: {target}")

    print("\n=== Summary ===")
    print("Examples saved to:", examples_dir)
    print("List of trajectory files:")
    for f in sorted(Path(".").glob("trajectory*.json")):
        print(f"  - {f} ({f.stat().st_mtime})")

if __name__ == "__main__":
    main()
