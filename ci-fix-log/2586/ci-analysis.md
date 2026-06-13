# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: numpy C头文件缺失
- 新模式症状关键词: numpy/arrayobject.h, No such file or directory, fatal error, make py

## 根因分析

### 直接错误
```
python/swigfaiss_wrap.cxx:3228:10: fatal error: numpy/arrayobject.h: No such file or directory
 3228 | #include <numpy/arrayobject.h>
      |          ^~~~~~~~~~~~~~~~~~~~~
compilation terminated.
make: *** [Makefile:84: python/_swigfaiss.so] Error 1
```

### 根因定位
- 失败位置: AI/faiss/20180223/24.03-lts-sp3/Dockerfile:14 (RUN 指令)
- 失败原因: `make py` 编译 faiss Python SWIG 绑定时，编译器找不到 numpy C 头文件 `numpy/arrayobject.h`。指令中硬编码的 include 路径 `-I/opt/conda/lib/python3.12/site-packages/numpy/core/include` 下不存在该文件。

### 与 PR 变更的关联
PR 新增了整个 Dockerfile（此前不存在 faiss 20180223 的构建文件）。**日志中实际执行的 RUN 命令与 PR diff 中的 RUN 命令存在显著差异**——diff 显示仅通过 conda 安装 faiss-cpu 预编译包，但日志显示实际执行的是从 GitHub 源码编译 faiss 的完整流程（包含 dnf 安装 gcc-c++/make/openblas-devel/swig、下载源码、make、make py 等）。该差异表明 CI 构建的 Dockerfile 与 PR diff 内容可能不一致。无论何种情况，失败均由本次 PR 新增内容引入。

## 修复方向

### 方向 1（置信度: 中）
在 `conda install -y python=3.12 numpy` 后，使用 `python3 -c "import numpy; print(numpy.get_include())"` 动态获取 numpy C 头文件的实际安装路径，再将其传入 `make py` 的 `PYTHONCFLAGS` 以替代硬编码路径 `-I/opt/conda/lib/python3.12/site-packages/numpy/core/include`。

### 方向 2（置信度: 低）
如果 CI 本应按照 PR diff 中的 Dockerfile 执行，即直接通过 `conda install -y -c pytorch -c conda-forge python=3.12 faiss-cpu=${VERSION}` 安装预编译包而非从源码编译，则无需处理头文件问题。但需确认 conda-forge 频道是否存在 `faiss-cpu=20180223` 版本，以及 CI 为何执行了不同于 diff 的 Dockerfile。

## 需要进一步确认的点
1. **Dockerfile 内容不一致**：CI 日志中实际执行的 RUN 命令（编译 faiss 源码）与 PR diff 中的 RUN 命令（conda 安装预编译包）完全不同。需要确认 CI 构建的 Dockerfile 是否与提交的 diff 一致，是否存在合并冲突或 CI 编排层面的错误。
2. **numpy 头文件实际路径**：在目标基础镜像中执行 `conda install -y numpy` 后，需用 `find /opt/conda -name arrayobject.h` 确认 `numpy/arrayobject.h` 的实际安装路径。
3. **conda-forge faiss-cpu 版本可用性**：若走 conda 直接安装路线，需验证 `conda-forge` 频道是否提供 `faiss-cpu=20180223` 版本。
