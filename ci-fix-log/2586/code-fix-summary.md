# 修复摘要

## 修复的问题
faiss 20180223 版本在 conda-forge 上不存在预编译包 `faiss-cpu=20180223`，改为从 GitHub 源码编译，并动态获取 numpy C 头文件路径以避免编译时 `numpy/arrayobject.h: No such file or directory` 错误。

## 修改的文件
- `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`: 将 conda 安装 faiss-cpu 预编译包的方式替换为从 GitHub 源码编译，通过 `$(python3 -c 'import numpy; print(numpy.get_include())')` 动态获取 numpy 头文件路径，写入 makefile.inc 中的 PYTHONCFLAGS，解决硬编码路径导致的编译失败。

## 修复逻辑
CI 分析报告指出，`faiss-cpu=20180223` 在 conda-forge 频道上不存在，CI 管道自动生成了一个源码编译的 Dockerfile，但其中 `makefile.inc` 里的 `PYTHONCFLAGS` 硬编码了错误的 numpy 头文件路径（`-I/opt/conda/lib/python3.12/site-packages/numpy/core/include`），导致 `make py` 编译 SWIG 绑定时报 `numpy/arrayobject.h: No such file or directory`。

修复方案：
1. 保留 conda 环境用于安装 python=3.12 和 numpy
2. 通过 yum 安装编译依赖（gcc, gcc-c++, make, openblas-devel, swig, git）
3. 从 GitHub 克隆 faiss v20180223 源码
4. 复制示例 makefile.inc.Linux 并追加动态获取的 PYTHONCFLAGS（使用 `python3 -c 'import numpy; print(numpy.get_include())'` 运行时获取实际路径）和 BLASLDFLAGS
5. 执行 `make && make py` 编译
6. 将生成的 `_swigfaiss.so` 和 `swigfaiss.py` 复制到 conda Python 的 site-packages 目录
7. 按项目规范仅移除 gcc 和 make，保留其他依赖

## 潜在风险
- ARM64 架构下，`makefile.inc.Linux` 中的 x86 特定编译标志（`-mavx -msse4 -mpopcnt`）可能导致编译失败，但本次 CI 失败仅涉及 amd64 架构，ARM64 兼容性需后续单独验证
- 如果 GitHub 仓库不可访问或 `v20180223` tag 被移除，`git clone` 步骤会失败
- `python3 setup.py install` 被移除（该版本无 setup.py），改为直接复制 .so/.py 文件到 site-packages，需确认 `swigfaiss.py` 与 `_swigfaiss.so` 的导入兼容性