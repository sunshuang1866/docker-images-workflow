# 修复摘要

## 修复的问题
conda 仓库中不存在 `faiss-cpu=20180223` 包版本，导致 Docker 构建失败。改为从 GitHub 源码编译安装。

## 修改的文件
- `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`: 将 conda 预编译包安装方式改为源码编译安装（git clone + make + make py）

## 修复逻辑
CI 分析报告指出根因是 `faiss-cpu=20180223` 在 conda 的 pytorch/conda-forge/defaults 三个 channel 中均不存在（该版本发布于 2018 年，早于 conda-forge 收录 faiss-cpu 包的时间）。修复方案将 x86_64/arm64 共用路径的安装方式从 `conda install faiss-cpu=${VERSION}` 改为从 GitHub 源码编译：
1. conda 仍安装 python=3.12 和 numpy（faiss 运行时依赖）
2. yum 安装编译工具链（git, make, gcc-c++, openblas-devel）
3. `git clone --branch v20180223` 获取 faiss 源码（该 tag 经验证存在于 facebookresearch/faiss 仓库）
4. 内联生成 makefile.inc 配置文件，指定 OpenBLAS 路径和 Python 3.12 头文件路径
5. `make` 编译 C++ 核心库，`make py` 编译 Python SWIG 绑定
6. 将生成的 faiss.py、swigfaiss.py、_swigfaiss.so 复制到 conda Python site-packages

编译标志中移除了 x86-only 的 `-mavx -msse4 -mpopcnt` 优化选项，确保在 arm64 架构上也能编译通过。

## 潜在风险
- openEuler 24.03 系统中 `/usr/lib64/libopenblas.so` 路径需与 makefile.inc 中硬编码的路径一致。若系统 openblas 安装路径为 `/usr/lib64/libopenblas.so.0` 或其他变体，构建可能失败，但 openEuler 24.03 的 openblas-devel 包一般提供该标准路径。
- 源码编译增加构建时间（约增加 5-10 分钟），但不影响最终镜像的运行时行为。
- numpy 头文件路径 `/opt/conda/lib/python3.12/site-packages/numpy/core/include/` 依赖 conda 安装的 numpy 版本，若 numpy 版本升级导致路径变化可能需调整。