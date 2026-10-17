"""核对 wheel、sdist 和由 sdist 重建的 wheel，确保发行物完整且一致。"""

import argparse
import hashlib
import json
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path
from typing import Dict


def read_artifact(path: Path) -> Dict[str, bytes]:
    """只读归档内容并统一 sdist 顶层目录及源码目录的路径。"""
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return {
                name: archive.read(name)
                for name in archive.namelist()
                if not name.endswith("/")
            }
    with tarfile.open(path) as archive:
        files = {}
        for member in archive.getmembers():
            if member.isfile():
                name = member.name.split("/", 1)[1]
                if name.startswith("src/"):
                    name = name[4:]
                stream = archive.extractfile(member)
                assert stream is not None
                files[name] = stream.read()
        return files


def verify_artifacts(directory: Path, rebuilt: Path, expected_version: str) -> None:
    """检查固定发布集合、元数据、许可证和上游资源哈希。"""
    wheels = sorted(directory.glob("*.whl"))
    sdists = sorted(directory.glob("*.tar.gz"))
    rebuilt_wheels = sorted(rebuilt.glob("*.whl"))
    assert len(wheels) == len(sdists) == len(rebuilt_wheels) == 1
    expected_name = f"mineru_magika-{expected_version}-py3-none-any.whl"
    assert wheels[0].name == rebuilt_wheels[0].name == expected_name
    assert sdists[0].name == f"mineru_magika-{expected_version}.tar.gz"
    resources = json.loads(Path(__file__).with_name("resource_hashes.json").read_text())
    archives = [read_artifact(path) for path in [*wheels, *sdists, *rebuilt_wheels]]
    payloads = []
    for files in archives:
        metadata_files = [
            name for name in files if name.endswith("/METADATA") or name == "PKG-INFO"
        ]
        assert len(metadata_files) == 1
        info = BytesParser().parsebytes(files[metadata_files[0]])
        assert info["Name"] == "mineru-magika"
        assert info["Version"] == expected_version
        assert info["Requires-Python"] == ">=3.8"
        assert info.get_all("Requires-Dist") == ["click>=8.1.7"]
        assert info.get_all("Provides-Extra") is None
        licenses = [data for name, data in files.items() if name.endswith("LICENSE")]
        assert len(licenses) == 1
        assert licenses[0] == Path(__file__).parents[1].joinpath("LICENSE").read_bytes()
        for name, expected_hash in resources.items():
            assert hashlib.sha256(files[name]).hexdigest() == expected_hash, name
        payloads.append(
            {name: data for name, data in files.items() if name.startswith("magika/")}
        )
    assert payloads[0] == payloads[1] == payloads[2], "Package payloads differ"
    print("Verified wheel, sdist and rebuilt wheel metadata, license and payload")


def main() -> None:
    """从命令行接收产物位置和期望版本。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--rebuilt", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    verify_artifacts(args.dist, args.rebuilt, args.expected_version)


if __name__ == "__main__":
    main()
