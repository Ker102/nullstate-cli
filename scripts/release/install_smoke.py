from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify nullstate installs and exposes the console command.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep the temporary build and virtualenv directory.")
    parser.add_argument("--tag", help="Install nullstate from the public GitHub repository at this tag instead of building a local wheel.")
    parser.add_argument("--package-spec", help="Install an explicit pip package spec instead of building a local wheel.")
    args = parser.parse_args()
    if args.tag and args.package_spec:
        parser.error("--tag and --package-spec are mutually exclusive.")

    repo_root = Path(__file__).resolve().parents[2]
    temp_context: tempfile.TemporaryDirectory[str] | None = tempfile.TemporaryDirectory(
        prefix="nullstate-install-smoke-"
    )
    temp_root = Path(temp_context.name)
    try:
        venv_dir = temp_root / "venv"
        package_spec = _resolve_package_spec(args.tag, args.package_spec, temp_root=temp_root, repo_root=repo_root)
        venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
        python = _venv_python(venv_dir)
        _run([str(python), "-m", "pip", "install", str(package_spec)], cwd=repo_root)
        nullstate = _console_script(venv_dir)
        _run([str(nullstate), "--help"], cwd=repo_root)
        _run([str(nullstate), "doctor", "--offline"], cwd=repo_root)
        print(f"Install smoke passed: {package_spec}")
        if args.keep_temp:
            print(f"Temporary artifacts kept at: {temp_root}")
            temp_context = None
        return 0
    finally:
        if temp_context is not None:
            temp_context.cleanup()


def _resolve_package_spec(tag: str | None, package_spec: str | None, *, temp_root: Path, repo_root: Path) -> str | Path:
    if tag:
        return f"git+https://github.com/Ker102/nullstate-cli.git@{tag}"
    if package_spec:
        return package_spec

    dist_dir = temp_root / "dist"
    _run([sys.executable, "-m", "build", "--outdir", str(dist_dir)], cwd=repo_root)
    wheels = sorted(dist_dir.glob("nullstate-*.whl"))
    if not wheels:
        raise SystemExit(f"No nullstate wheel produced in {dist_dir}")
    return wheels[0]


def _run(command: list[str], *, cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        raise SystemExit(completed.returncode)


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _console_script(venv_dir: Path) -> Path:
    scripts_dir = venv_dir / ("Scripts" if sys.platform == "win32" else "bin")
    script_name = "nullstate.exe" if sys.platform == "win32" else "nullstate"
    script = scripts_dir / script_name
    if script.is_file():
        return script
    discovered = shutil.which("nullstate", path=str(scripts_dir))
    if discovered:
        return Path(discovered)
    raise SystemExit(f"nullstate console command not found in {scripts_dir}")


if __name__ == "__main__":
    raise SystemExit(main())
