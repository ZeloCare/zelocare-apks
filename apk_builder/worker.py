"""Runs in a short-lived Kubernetes Job; build output is published to GitHub Releases."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/work")

def run(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True)

def build(app: str, ref: str):
    source = ROOT / app
    run("git", "clone", "--depth", "1", "--branch", ref, f"https://x-access-token:{os.environ['SOURCE_REPOS_TOKEN']}@github.com/ZeloCare/{app}.git", str(source))
    run("npm", "ci", "--legacy-peer-deps", cwd=source)
    run("npx", "tsc", "--noEmit", cwd=source)
    if app == "zelocare-mobile": run("npx", "jest", "--passWithNoTests", "--runInBand", cwd=source)
    run("npx", "expo", "prebuild", "--platform", "android", "--non-interactive", cwd=source)
    run("./gradlew", "--no-daemon", "assembleRelease", cwd=source / "android")

if __name__ == "__main__":
    selected = os.environ["BUILD_APP"]
    targets = []
    if selected in ("all", "zelocare-mobile"): targets.append(("zelocare-mobile", os.environ["MOBILE_REF"]))
    if selected in ("all", "zelocare-volunteer"): targets.append(("zelocare-volunteer", os.environ["VOLUNTEER_REF"]))
    for app, ref in targets: build(app, ref)
