# CI 失败分析报告

## 基本信息
- PR: #3016 — chore(ambertools): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Python 3.13 C API 不兼容
- 新模式症状关键词: _PyList_Extend, _PyInterpreterState_GetConfig, _PyUnicode_FastCopyCharacters, _PyLong_AsByteArray, _PyGen_SetStopIterationValue, not declared in this scope, too few arguments, python3.13, Cython

## 根因分析

### 直接错误

```
pytraj/trajectory/frame.cpp:3159:22: error: '_PyList_Extend' was not declared in this scope; did you mean 'PyList_Extend'?
pytraj/trajectory/frame.cpp:3180:39: error: '_PyInterpreterState_GetConfig' was not declared in this scope; did you mean 'PyInterpreterState_GetID'?
pytraj/trajectory/frame.cpp:39829:13: error: '_PyUnicode_FastCopyCharacters' was not declared in this scope; did you mean 'PyUnicode_CopyCharacters'?
pytraj/trajectory/frame.cpp:43677:46: error: too few arguments to function 'int _PyLong_AsByteArray(PyLongObject*, unsigned char*, size_t, int, int, int)'
pytraj/trajectory/frame.cpp:44757:13: error: '_PyGen_SetStopIterationValue' was not declared in this scope; did you mean '__Pyx_PyGen__FetchStopIterationValue'?
error: command '/usr/bin/g++' failed with exit code 1
make[2]: *** [AmberTools/src/pytraj/CMakeFiles/pytraj.dir/build.make:535: .../pytraj-build.stamp] Error 1
make: *** [Makefile:156: all] Error 2
```

### 根因定位

- 失败位置: `pytraj/trajectory/frame.cpp`（AmberTools 24 源码中 pytraj 组件的 Cython 预生成 C++ 文件）
- 失败原因: `UseMiniconda.cmake` 从 conda-forge 下载最新版 Miniforge3，其内置 Python 3.13 移除了多个 Python 内部私有 C API（`_PyList_Extend`、`_PyInterpreterState_GetConfig`、`_PyUnicode_FastCopyCharacters`、`_PyGen_SetStopIterationValue`）并修改了 `_PyLong_AsByteArray` 的函数签名。AmberTools 24 源码中的 pytraj 预生成 C++ 代码依赖这些已被移除/修改的 API，导致 g++ 编译失败。

### 与 PR 变更的关联

**直接关联。** PR 新增的 `UseMiniconda.cmake` 文件（`HPC/ambertools/24.8/24.03-lts-sp4/UseMiniconda.cmake`）通过 `Miniforge3-${CONTINUUM_SYSTEM_NAME}-${CONTINUUM_BITS}.sh` 动态下载 Miniforge3 最新版。在 2026 年 7 月份，当前最新版 Miniforge3 默认内置 Python 3.13，而 AmberTools 24 的 pytraj 源码中的 `frame.cpp` 等 Cython 预生成文件是针对 Python 3.11/3.12 的 C API 生成的，与 Python 3.13 不兼容。

证据链：
1. 日志中编译器 include 路径指向 `python3.13`：`-I/opt/amber24_src/build/CMakeFiles/miniconda/install/include/python3.13`
2. 构建产物目录名含 `cpython-313`：`lib.linux-x86_64-cpython-313`
3. 所有编译错误均为 Python 3.13 中已移除/变更的私有 C API 符号

## 修复方向

### 方向 1（置信度: 高）

在 `UseMiniconda.cmake` 或 Dockerfile 中锁定 Miniforge3 的 Python 版本为 3.12（或 3.11），而非拉取最新版。具体做法：环境变量中指定 `MINICONDA_VERSION` 为 `py312` 对应的版本号，或将 Miniforge3 下载 URL 从 `latest/download` 改为固定版本 URL（如 `24.3.0-0`，该版本内置 Python 3.12）。

### 方向 2（置信度: 中）

在 Dockerfile 的 `make install` 前，安装与 Python 3.13 兼容的新版 Cython，并强制重新 Cythonize pytraj 的 `.pyx` 文件（即删除预生成的 `frame.cpp` 等，让 Cython 重新从 `.pyx` 源文件生成 C++ 代码），使生成的代码适配 Python 3.13 C API。此方案风险较高，因为新版 Cython 可能引入其他兼容性问题，且 AmberTools 24 的 `.pyx` 文件可能本身也需要适配修改。

## 需要进一步确认的点

1. 现有 `24.03-lts-sp2` 镜像是否也使用相同的 `UseMiniconda.cmake`？如果 sp2 镜像构建成功时的 Miniforge3 版本内置的 Python 版本是 3.11 或 3.12，则确认了"锁定 Python 版本"方案的可行性。
2. 确认 Miniforge3 哪个具体 release 版本内置 Python 3.12（如 `Miniforge3-24.3.0-0`），该版本是否在 conda-forge GitHub releases 中持续可用（不会被 latest 滚动覆盖导致 404）。
3. 是否需要为 aarch64 架构单独验证 Python 版本兼容性。

## 修复验证要求

若采用方向 1，code-fixer 必须：
1. 从 conda-forge/miniforge GitHub Releases 页面确认目标版本（如 24.3.0-0）的安装脚本文件名在 Linux x86_64 和 aarch64 两个架构上均存在；
2. 修改 `UseMiniconda.cmake` 中的 `INSTALLER_URL` 从 `latest/download` 改为固定版本路径后，在 x86_64 和 aarch64 的 Docker build 中验证 Miniforge3 能正常下载、安装并完成 pytraj 编译。
