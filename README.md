# mineru-magika

A Python-only fork of [Google Magika](https://github.com/google/magika), based on
[the published 1.0.3 source](https://github.com/google/magika/tree/9f225aa480e675af44343b9160f077073ed1b752).
The distribution is named **mineru-magika**; the Python import remains **magika**.
This fork is maintained independently and is not an official Google release.

## Installation

Choose one ONNX Runtime distribution yourself. This package only installs
`click>=8.1.7`; it does **not** install ONNX Runtime, DirectML, or GPU extras.

```sh
# CPU runtime (choose a version compatible with your Python/platform)
pip install mineru-magika onnxruntime

# Windows x64, Python 3.10–3.14
pip install mineru-magika "onnxruntime-directml>=1.23,<2"
```

Python >=3.8 is supported when a compatible ONNX Runtime is installed. Without a
runtime, installation succeeds but importing `magika` fails with a missing
`onnxruntime` module. There is no runtime download or automatic backend selection.

Do not install `magika` and `mineru-magika` together: they own the same Python
namespace. In an existing environment, uninstall `magika` before installing this
fork. A downstream requirement for the distribution `magika` must also be changed;
installing this fork does not satisfy that requirement automatically.

## Python API and CLI

```python
from magika import Magika

result = Magika().identify_bytes(b"function log(msg) {console.log(msg);}")
print(result.output.label)  # javascript
```

```sh
magika-python-client --version
magika-python-client path/to/file
```

As in the upstream pure-Python wheel, `magika` prints a warning directing you to
`magika-python-client` and exits with status 1. No Rust executable is bundled.
The Python API, model, configuration and classification behavior are unchanged.
The upstream `CPUExecutionProvider` selection is retained, including when using
the DirectML distribution; this fork does not enable GPU inference.

## Fork changes and provenance

Version 1.0.3 uses upstream commit `9f225aa480e675af44343b9160f077073ed1b752`.
Changes are limited to distribution metadata, caller-managed runtime dependencies,
distribution version lookups, Python-only packaging, documentation and CI.
Model and configuration SHA-256 values are recorded in
`python/scripts/resource_hashes.json` in the source repository and checked against
installed artifacts. Original source copyright notices and the Apache-2.0 license
are retained. The upstream multi-language sources remain for provenance but are
not included in the Python distributions.

## Development and release

From the repository's `python` directory:

```sh
uv sync --locked
uv pip install onnxruntime
uv run --no-sync pytest tests
uv build
```

CI builds a universal wheel and sdist, rebuilds the wheel from the sdist, and tests
normal installation without any runtime. CPU checks cover Windows, Linux and
macOS on Python 3.10–3.14, plus Linux 3.8/3.9. Windows x64 also checks environments
containing only the DirectML distribution. Linux Python 3.12 runs the upstream
Python regression suite. Runtime dependencies are installed explicitly by CI.

Tags matching `v<version>` publish the exact tested artifacts through GitHub
Trusted Publishing. Configure the PyPI pending publisher with project
`mineru-magika`, owner `myhloli`, repository `mineru-magika`, workflow `publish.yml`
and environment `pypi`. Publishing requires all validation jobs to pass.
