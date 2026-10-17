"""验证已安装发行包的依赖、资源、版本与实际推理行为。"""

import argparse
import hashlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
from pathlib import Path


def verify_distribution(expected_version: str, runtime: str) -> None:
    """在隔离环境检查安装结果，避免同名模块或其他 ORT 包掩盖缺陷。"""
    distribution = metadata.distribution("mineru-magika")
    assert distribution.version == expected_version
    assert distribution.requires == ["click>=8.1.7"], distribution.requires
    names = {
        item.metadata["Name"].lower().replace("_", "-")
        for item in metadata.distributions()
    }
    assert "magika" not in names, "Upstream magika must not be co-installed"
    expected_runtimes = {
        "none": set(),
        "cpu": {"onnxruntime"},
        "directml": {"onnxruntime-directml"},
    }
    assert {name for name in names if name.startswith("onnxruntime")} == (
        expected_runtimes[runtime]
    ), names
    resources = json.loads(Path(__file__).with_name("resource_hashes.json").read_text())
    for resource, expected_hash in resources.items():
        installed = Path(distribution.locate_file(resource))
        assert installed.is_file(), resource
        assert hashlib.sha256(installed.read_bytes()).hexdigest() == expected_hash, (
            resource
        )
    entry_points = {entry.name: entry.value for entry in distribution.entry_points}
    assert entry_points == {
        "magika-python-client": "magika.cli.magika_client:main",
        "magika": "magika.cli.magika_rust_client_not_found_warning:main",
    }, entry_points
    if runtime == "none":
        print("Verified normal installation without any ONNX Runtime distribution")
        return

    # 只在调用方显式安装运行时后加载模块，默认安装检查不依赖 ORT。
    import onnxruntime

    import magika

    assert magika.__version__ == expected_version
    assert (
        Path(magika.__file__).resolve()
        == Path(distribution.locate_file("magika/__init__.py")).resolve()
    ), "The test must import the installed artifact"
    assert "CPUExecutionProvider" in onnxruntime.get_available_providers()
    classifier = magika.Magika()
    assert classifier.get_module_version() == expected_version
    sample = b"function log(msg) {console.log(msg);}"
    result = classifier.identify_bytes(sample)
    assert result.ok and result.output.label == "javascript", result
    assert result.dl.label == "javascript", "Exercise ONNX inference, not a heuristic"
    client = shutil.which("magika-python-client")
    assert client is not None
    version = subprocess.run(
        [client, "--version"], check=True, capture_output=True, text=True
    )
    assert expected_version in version.stdout, version
    placeholder = shutil.which("magika")
    assert placeholder is not None
    warning = subprocess.run([placeholder, "--version"], capture_output=True, text=True)
    assert warning.returncode == 1 and "magika-python-client" in warning.stdout
    print(
        f"Verified {distribution.metadata['Name']} {expected_version}; "
        f"runtime={runtime}; providers={onnxruntime.get_available_providers()}"
    )


def main() -> None:
    """解析发布验证参数并执行对应的安装契约检查。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument(
        "--runtime", choices=("none", "cpu", "directml"), default="none"
    )
    args = parser.parse_args()
    verify_distribution(args.expected_version, args.runtime)


if __name__ == "__main__":
    main()
