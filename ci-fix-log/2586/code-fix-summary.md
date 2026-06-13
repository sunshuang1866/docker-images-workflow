# 修复摘要

## 修复的问题
faiss 20180223 版本的 Dockerfile 因 conda 无此版本的 faiss-cpu 包且源码编译时错误地假设 `python/setup.py` 存在而构建失败，改为正确的源码编译 + `make py` 方式构建 Python 绑定。

## 修改的文件
- `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`: 将 `conda install faiss-cpu=20180223` 替换为完整的源码编译流程，使用 `make py` 构建 Python 绑定（而非不存在的 `python setup.py install`），增加构建依赖（gcc-c++、make、openblas-devel、swig），设置 LD_LIBRARY_PATH 确保共享库可被找到。

## 修复逻辑
1. **根因**：faiss-cpu 在 conda-forge/pytorch 频道中不存在版本 20180223（最早的 faiss conda 包从 0.1/1.2.1 开始，均为语义化版本号）。即使使用源码编译，faiss v20180223 的 `python/` 目录下没有 `setup.py`，其 Python 绑定通过 SWIG + Makefile 构建，应使用 `make py` 命令。
2. **修复方案**：保留 miniconda 提供的 Python 3.12/numpy 环境，通过 dnf 安装编译工具，从 GitHub 下载 faiss v20180223 源码，使用正确的构建流程（`make` 编译 C++ 库 + `make py` 构建 Python 绑定），将生成的 `_swigfaiss.so`、`faiss.py`、`swigfaiss.py` 复制到 conda 的 site-packages 目录，并将 `libfaiss.so` 复制到 conda lib 目录并设置 LD_LIBRARY_PATH。

## 潜在风险
- 源码编译增加了构建时间和层大小，且依赖网络下载 GitHub 源码（可能受网络波动影响）。
- `makefile.inc.Linux` 模板中的 CFLAGS 原本包含 x86_64 特定标志（`-m64 -mavx -msse4 -mpopcnt`），已被通用标志替代以满足跨架构兼容，但未在 ARM64 上实际验证。
- 若 faiss v20180223 源码的 Makefile 对 Python 3.12 存在兼容性问题，构建仍可能失败。