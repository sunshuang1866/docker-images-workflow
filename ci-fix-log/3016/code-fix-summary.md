# 修复摘要

## 修复的问题
将 Miniforge3 下载 URL 从 `latest` 滚动版本锁定为固定版本 `24.3.0-0`，解决 Python 3.13 私有 C API 不兼容导致的 pytraj 编译失败。

## 修改的文件
- `HPC/ambertools/24.8/24.03-lts-sp4/UseMiniconda.cmake`: 将 `INSTALLER_URL` 中的 `releases/latest/download/` 改为 `releases/download/24.3.0-0/`

## 修复逻辑
分析报告指出根因是 `UseMiniconda.cmake` 通过 `/latest/download/` 路径动态下载最新版 Miniforge3，而 2026 年 7 月最新版内置 Python 3.13，移除了 AmberTools 24 pytraj 预生成 C++ 代码依赖的私有 C API（`_PyList_Extend`、`_PyInterpreterState_GetConfig`、`_PyUnicode_FastCopyCharacters`、`_PyGen_SetStopIterationValue` 等），导致 g++ 编译失败。修复方案为锁定 Miniforge3 版本至 `24.3.0-0`（该版本内置 Python 3.12），与 AmberTools 24 的 Cython 预生成代码兼容。

已从上游 `conda-forge/miniforge` 的 tag `24.3.0-0` 验证：`Miniforge3-Linux-x86_64.sh` 和 `Miniforge3-Linux-aarch64.sh` 均存在且可下载。

## 潜在风险
- Miniforge3 24.3.0-0 的 conda 包索引可能随时间更新，导致后续 `conda install` 步骤安装的某些包版本变化（但 Python 主版本锁定在 3.12，不会引入 3.13 的 API 不兼容问题）
- 若未来 24.3.0-0 版本从 GitHub Releases 中被移除，需要更新 `INSTALLER_URL` 中的版本号