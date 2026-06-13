# 修复摘要

## 修复的问题
faiss v20180223 在 aarch64 架构上编译失败，原因是 Makefile 硬编码了 x86_64 专用编译器标志（-m64、-mavx、-msse4、-mpopcnt），g++ 在 aarch64 上无法识别。

## 修改的文件
- `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`: 在 conda install 步骤中按架构分支处理 — amd64 保持原有 conda 安装方式，arm64 改为手动编译 faiss 并移除 x86_64 专用标志。

## 修复逻辑
分析报告指出根因是 faiss v20180223（2018 年极旧版本）的 `example_makefiles/makefile.inc.Linux` 硬编码了 `-m64`、`-mavx`、`-msse4`、`-mpopcnt` 等 x86_64 专用编译选项，在 aarch64 上 g++ 报 unrecognized command-line option 错误。

修复方案：利用 Dockerfile 已有的 `TARGETARCH` 变量进行架构判断：
- **amd64**：保持原逻辑，通过 `conda install -c pytorch -c conda-forge faiss-cpu=${VERSION}` 安装预编译包
- **arm64**：安装编译依赖（openblas-devel、gcc-c++、git、make），通过 conda 安装 python 和 numpy，克隆 faiss 源码，用 sed 移除 makefile.inc.Linux 中的 x86_64 专用标志（`-m64`、`-mavx`、`-msse4`、`-mpopcnt`），然后编译 C++ 库并安装 Python 绑定

## 潜在风险
- arm64 路径依赖 openEuler 24.03-LTS-SP3 仓库中的 `openblas-devel` 和 `gcc-c++` 包，若源不可用则构建失败
- `git clone` 深度克隆依赖 GitHub 可访问性，网络问题可能导致构建失败
- faiss v20180223 的 `python setup.py install` 步骤可能因 aarch64 Python 兼容性问题失败（如 swig 生成的包装代码不兼容 ARM），虽然编译阶段已通过标志修复，但运行时行为未经充分测试