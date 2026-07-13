# 修复摘要

## 修复的问题
移除 `cython=0.29` 的版本 pin，修复因 Miniforge3 默认 Python 3.13 与 `cython=0.29`（仅支持到 Python 3.12）不兼容导致的 conda 依赖解析失败。

## 修改的文件
- `HPC/ambertools/24.8/24.03-lts-sp4/UseMiniconda.cmake`: 第 174 行，将 `cython=0.29` 改为 `cython`（移除版本约束）

## 修复逻辑
CI 失败的直接原因是 `LibMambaUnsatisfiableError`：`cython=0.29` 在 conda-forge 中最高仅支持 Python 3.12，无法与 Miniforge3 默认的 Python 3.13 兼容。将 `cython=0.29` 改为 `cython` 后，conda 解析器会自动选择与当前 Python 版本兼容的最新 cython 构建。此修改与 sp4 版本中已对 `numpy` 做的同类处理（相比 sp2 版本已移除 `numpy=1.26.4` 的 pin）保持一致。

## 潜在风险
- AmberTools 24 的 Cython 扩展模块构建可能与 cython 3.x 存在 API 兼容性问题，但上游 conda-forge 已不再为 cython 0.29 提供 Python 3.13 构建，放弃版本 pin 是唯一可行方案。
- 若后续编译阶段出现 cython 版本不兼容错误，需进一步调整 AmberTools 源码中的 `.pyx` 文件，但此风险在当前阶段无法规避。