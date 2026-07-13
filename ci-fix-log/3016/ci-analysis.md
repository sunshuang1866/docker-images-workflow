# CI 失败分析报告

## 基本信息
- PR: #3016 — chore(ambertools): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Conda包版本冲突
- 新模式症状关键词: LibMambaUnsatisfiableError, numpy=1.26.4, python=3.13, Solving environment: failed, CMake Error at cmake/UseMiniconda.cmake

## 根因分析

### 直接错误
```
#12 136.9 Solving environment: ...working... failed
#12 551.4 LibMambaUnsatisfiableError: Encountered problems while solving:
#12 551.4   - package numpy-1.26.4-py310hb13e2d6_0 requires python >=3.10,<3.11.0a0, but none of the providers can be installed
#12 551.4 Could not solve for environment specs
#12 551.4 The following packages are incompatible
#12 551.4 ├─ numpy =1.26.4 * is installable with the potential options
#12 551.4 │  ├─ numpy 1.26.4 would require
#12 551.4 │  │  └─ python >=3.10,<3.11.0a0 *, which can be installed;
#12 551.4 │  ├─ numpy 1.26.4 would require
#12 551.4 │  │  └─ python >=3.11,<3.12.0a0 *, which can be installed;
#12 551.4 │  ├─ numpy 1.26.4 would require
#12 551.4 │  │  └─ python >=3.12,<3.13.0a0 *, which can be installed;
#12 551.4 │  └─ numpy 1.26.4 would require
#12 551.4 │     └─ python >=3.9,<3.10.0a0 *, which can be installed;
#12 551.4 └─ pin on python =3.13 * is not installable because it requires
#12 551.4    └─ python =3.13 *, which conflicts with any installable versions previously reported.
#12 551.4 Pins seem to be involved in the conflict. Currently pinned specs:
#12 551.4  - python=3.13
```

### 根因定位
- 失败位置: `HPC/ambertools/24.8/24.03-lts-sp4/UseMiniconda.cmake:177`
- 失败原因: `UseMiniconda.cmake` 中硬编码了 `numpy=1.26.4`，但 openEuler 24.03-LTS-SP4 基础镜像的 Miniforge3 默认安装 Python 3.13，而 numpy 1.26.4 在 conda-forge 上仅提供 Python 3.9~3.12 的构建，无 Python 3.13 版本，导致 conda 依赖求解失败。

### 与 PR 变更的关联
PR 新增了 `UseMiniconda.cmake` 文件（268 行），该文件直接从上游 AmberTools 24 源码中复用，其第 177 行附近的 `execute_process(COMMAND ${CONDA} install -y -q conda-build numpy=1.26.4 ...)` 将 numpy 版本锁定为 1.26.4。openEuler 24.03-LTS-SP4 是较新的基础镜像，其 Miniforge3 默认提供的 Python 版本为 3.13，而 numpy 1.26.4 不兼容 Python 3.13。对比已有的 `24.03-lts-sp2` 版本（使用更旧的基础镜像，Python 版本可能更低），此问题仅在 SP4 新镜像上暴露。

## 修复方向

### 方向 1（置信度: 高）
将 `UseMiniconda.cmake` 中 `numpy=1.26.4` 的硬编码版本约束移除或放宽。可以改为不指定版本（让 conda 自动求解兼容版本），或升级到支持 Python 3.13 的较新 numpy 版本（如 `numpy>=1.26.4` 或明确指定 2.x 系列）。同时需要验证 AmberTools 24 是否兼容新版本 numpy。

### 方向 2（置信度: 中）
修改 `UseMiniconda.cmake` 的 Miniforge3 安装阶段，指定安装较低版本的 Python（如 3.12），以匹配合 numpy 1.26.4 的可用构建。此方向可能更安全（不改变 AmberTools 的 Python 依赖面），但需要确认 Miniforge3 安装器是否支持指定 Python 版本。

## 需要进一步确认的点
1. AmberTools 24.8 的官方文档或构建脚本是否对 numpy 版本有硬性要求（即是否必须 1.26.x），还是可以任意升级。
2. 已有的 `HPC/ambertools/24.8/24.03-lts-sp2/UseMiniconda.cmake` 在 SP2 基础镜像上构建成功时，Miniforge3 实际安装的 Python 版本是什么——这有助于判断是否需要用方向 2 在 SP4 上降级 Python。

## 修复验证要求
若采用方向 1（升级 numpy 版本约束），code-fixer 必须在提交前验证：
1. 从 AmberTools 24 上游源码确认 `numpy=1.26.4` 是否有硬性依赖理由（检查 `CMakeLists.txt` 及相关 Python 脚本中是否有 `numpy<=1.26.x` 或 API 版本约束）。
2. 构建完成后执行 `amber.python -c "import numpy; print(numpy.__version__)"` 确认 numpy 可正常导入，且版本满足 AmberTools 各工具的最低要求。
