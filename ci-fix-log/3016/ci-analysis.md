# CI 失败分析报告

## 基本信息
- PR: #3016 — chore(ambertools): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Conda版本约束冲突
- 新模式症状关键词: LibMambaUnsatisfiableError, cython=0.29, python=3.13, Solving environment failed, conda-forge

## 根因分析

### 直接错误
```
#12 96.66 Solving environment: ...working... failed
#12 230.1 LibMambaUnsatisfiableError: Encountered problems while solving:
#12 230.1   - package cython-0.29-py27hf484d3e_1000 requires python >=2.7,<2.8.0a0, but none of the providers can be installed
#12 230.1 Could not solve for environment specs
#12 230.1 The following packages are incompatible
#12 230.1 ├─ cython =0.29 * is installable with the potential options
#12 230.1 │  ├─ cython [0.29|0.29.1|...|0.29.9] would require
#12 230.1 │  │  └─ python >=2.7,<2.8.0a0 *, which can be installed;
#12 230.1 ...
#12 230.1 │  └─ cython [0.29.36|0.29.37] would require
#12 230.1 │     └─ python [>=3.12,<3.13.0a0 *|>=3.12.0rc3,<3.13.0a0 *], which can be installed;
#12 230.1 └─ pin on python =3.13 * is not installable because it requires
#12 230.1    └─ python =3.13 *, which conflicts with any installable versions previously reported.
#12 230.3 CMake Error at cmake/UseMiniconda.cmake:177 (message):
#12 230.3   Installation of packages failed! Please fix what's wrong, or disable Miniconda.
```

### 根因定位
- 失败位置: `HPC/ambertools/24.8/24.03-lts-sp4/UseMiniconda.cmake:177`（copied into `amber24_src/cmake/UseMiniconda.cmake`）
- 失败原因: Dockerfile 中 `./run_cmake` 步骤触发 `download_and_use_miniconda` 函数，该函数从 GitHub 下载最新 Miniforge3 安装包，默认带 Python 3.13。随后执行 `conda install cython=0.29` 时，conda-forge 仓库中 cython 0.29 系列最高仅支持到 Python 3.12，无 python=3.13 兼容构建，导致 conda 依赖解析失败。

### 与 PR 变更的关联
**高度相关。** 此次 PR 新增的 `UseMiniconda.cmake` 文件（第 177 行附近）硬编码了 `cython=0.29` 版本约束。当基础镜像 `openeuler:24.03-lts-sp4` 上的 Miniforge3 下载到的是最新版本（Python 3.13）时，该版本约束与 Python 3.13 不兼容。问题出在新引入的 UseMiniconda.cmake 中固化的 conda 包约束随上游 conda-forge Python 版本演进已过时。

## 修复方向

### 方向 1（置信度: 高）
将 `UseMiniconda.cmake` 中 `cython=0.29` 的版本 pin 移除或升级为与 Python 3.13 兼容的版本（如 `cython>=3.0` 或完全去掉版本约束改为 `cython`）。同时检查其他硬编码的 conda 包（如 `numpy=1.26.4`）是否也存在 Python 3.13 兼容性问题。

### 方向 2（置信度: 中）
在 Dockerfile 的 `cmake` 调用前通过 `-DMINICONDA_VERSION=<older_version>` 参数（或其他方式）强制 Miniforge3 下载一个内置 Python 3.12 的旧版本，使 `cython=0.29` 能够安装。此方案风险在于旧版 Miniforge3 的下载 URL 未来也可能被废弃。

## 需要进一步确认的点
1. AmberTools 24 对 cython 的实际最低版本需求（可能高版本 cython 也能满足其编译需求）。
2. `numpy=1.26.4` 是否同样与 Python 3.13 存在兼容性问题（日志中未报但可能同样冲突）。
3. AmberTools 24 上游是否提供了更新的 `UseMiniconda.cmake` 模板（其官方源码中的 cmake 文件可能已修正此问题）。

## 修复验证要求
1. code-fixer 必须验证修改后的 conda 包版本组合（cython、numpy、scipy 等）在 Python 3.13 环境（由最新 Miniforge3 提供）下能否成功解析。可在本地 `openeuler:24.03-lts-sp4` 容器中模拟 `conda install` 命令进行验证。
2. 修改 `UseMiniconda.cmake` 后，需确认 AmberTools 24 的后续 cmake 配置和 `make install` 能完整通过。
