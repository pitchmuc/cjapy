"""Install a wheel and sdist separately and smoke-test outside the checkout."""

import argparse
import ast
from pathlib import Path
import subprocess
import sys
import tempfile
import venv


SMOKE_TEST = r"""
import importlib.metadata
import importlib.util
from pathlib import Path
import socket
import sys
import sysconfig


def no_network(*args, **kwargs):
    raise AssertionError("Import smoke checks must not access the network")


socket.getaddrinfo = no_network
socket.socket.connect = no_network

import cjapy
from cjapy.connector import AdobeRequest

installed = Path(cjapy.__file__).resolve()
site_packages = Path(sysconfig.get_path("purelib")).resolve()
assert installed.is_relative_to(site_packages), installed
assert not installed.is_relative_to(Path(sys.argv[2]).resolve()), installed
metadata = importlib.metadata.distribution("cjapy")
assert installed == Path(metadata.locate_file("cjapy/__init__.py")).resolve()
assert cjapy.__version__ == metadata.version == sys.argv[1]
assert importlib.util.find_spec("pytest") is None, "pytest leaked into the runtime install"
assert "dynamic" not in metadata.metadata.get_all("Provides-Extra", [])
assert "test" in metadata.metadata.get_all("Provides-Extra", [])
print("Installed", metadata.metadata["Name"], metadata.version, "from", installed)
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist_dir", type=Path)
    args = parser.parse_args()
    dist_dir = args.dist_dir.resolve()
    root = Path(__file__).resolve().parents[1]
    # Read the version literal without importing the source package or its dependencies.
    version_module = ast.parse((root / "cjapy" / "__version__.py").read_text())
    expected_version = next(
        ast.literal_eval(node.value)
        for node in version_module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__version__"
                for target in node.targets)
    )

    artifacts = []
    for pattern in ("cjapy-*.whl", "cjapy-*.tar.gz"):
        matches = list(dist_dir.glob(pattern))
        if len(matches) != 1:
            parser.error("Expected exactly one {} in {}; use a clean output directory".format(
                pattern, dist_dir
            ))
        artifacts.append(matches[0])

    for artifact in artifacts:
        with tempfile.TemporaryDirectory(prefix="cjapy-install-") as temporary:
            work = Path(temporary).resolve()
            environment = work / "venv"
            venv.EnvBuilder(with_pip=True, symlinks=sys.platform != "win32").create(environment)
            python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            print("Checking", artifact.name, flush=True)
            subprocess.run(
                [str(python), "-I", "-m", "pip", "install", "--no-input",
                 "--disable-pip-version-check", str(artifact)],
                cwd=work, check=True,
            )
            subprocess.run(
                [str(python), "-I", "-m", "pip", "check"], cwd=work, check=True,
            )
            # -I ignores PYTHONPATH and removes the working directory from sys.path.
            # cwd is also outside the checkout; the smoke code checks the resolved path.
            subprocess.run(
                [str(python), "-I", "-c", SMOKE_TEST, expected_version, str(root)],
                cwd=work, check=True,
            )


if __name__ == "__main__":
    main()
