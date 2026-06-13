# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: numpy头文件路径不匹配
- 新模式症状关键词: numpy/arrayobject.h, No such file or directory, make py, swigfaiss

## 根因分析

### 直接错误
```
#8 724.0 g++ -I. -fPIC -m64 -Wall -g -O3 ... -I/opt/conda/lib/python3.12/site-packages/numpy/core/include -shared \
#8 724.0 -o python/_swigfaiss.so python/swigfaiss_wrap.cxx libfaiss.a /usr/lib64/libopenblas.so.0
#8 724.0 python/swigfaiss_wrap.cxx:3228:10: fatal error: numpy/arrayobject.h: No such file or directory
#8 724.0  3228 | #include <numpy/arrayobject.h>
#8 724.0       |          ^~~~~~~~~~~~~~~~~~~~~
#8 724.0 compilation terminated.
#8 724.1 make: *** [Makefile:84: python/_swigfaiss.so] Error 1
```

### 根因定位
- 失败位置: `python/swigfaiss_wrap.cxx:3228`（faiss 源码中的 SWIG 生成文件）
- 失败原因: `make py` 阶段使用的 numpy 头文件包含路径 `-I/opt/conda/lib/python3.12/site-packages/numpy/core/include` 中不存在 `numpy/arrayobject.h`。conda 安装的 numpy（可能为 2.x 版本）将头文件目录从 `numpy/core/include` 改为 `numpy/_core/include`，导致硬编码的旧路径无效。

### 与 PR 变更的关联

**重要发现：PR diff 与 CI 实际运行的 Dockerfile 不符。**

- PR diff 中的 Dockerfile（`AI/faiss/20180223/24.03-lts-sp3/Dockerfile`）使用 `conda install -y -c pytorch -c conda-forge python=3.12 faiss-cpu=${VERSION}` 从 conda 直接安装预编译的 faiss-cpu 包，无需编译。
- 但 CI 实际运行的 Dockerfile 却采用了从 GitHub 下载 faiss 源码并调用 `make` + `make py` 的编译安装方式。运行在 CI 中的 RUN 命令为：
  ```dockerfile
  RUN conda install -y python=3.12 numpy && ... && \
      make -j$(nproc) ... && \
      make py PYTHONCFLAGS="...-I/opt/conda/lib/python3.12/site-packages/numpy/core/include" && ...
  ```
- **CI 测试的 Dockerfile 与 PR diff 提交的 Dockerfile 不是同一版本**。PR 提交的是 conda 直接安装方式（理论上不会触发编译错误），但 CI 构建时使用的是包含源码编译逻辑的 Dockerfile。失败的直接原因是该编译版 Dockerfile 中 `numpy/core/include` 路径与当前 conda 实际安装的 numpy 头文件位置不匹配。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 RUN 命令中，将 `make py` 的 numpy 头文件包含路径从硬编码的 `numpy/core/include` 改为动态获取：
- 使用 `python -c "import numpy; print(numpy.get_include())"` 获取正确的 numpy 头文件路径，传入 `PYTHONCFLAGS`。
- 或者，在 `conda install` 时固定 numpy 版本为 1.x（如 `numpy=1.26`），使其头文件仍位于传统 `numpy/core/include` 路径。

### 方向 2（置信度: 中）
确认 CI 应该运行的 Dockerfile 版本。如果 PR 意图是使用 conda 直接安装（如 PR diff 所示），则应确保 CI 使用 PR diff 中的 Dockerfile 版本，即 `conda install -y -c pytorch -c conda-forge python=3.12 faiss-cpu=${VERSION}`，不进行源码编译。这样可以完全绕过编译错误。

## 需要进一步确认的点
1. CI 实际运行的 Dockerfile 与 PR diff 中的 Dockerfile 不一致，需要确认：CI 流水线是否在构建前对 Dockerfile 进行了自动改写？或者 PR 是否有后续提交未反映在提供的 diff 中？
2. 需确认 `conda install -y python=3.12 numpy` 实际安装的 numpy 版本号，以验证头文件路径布局（`core/include` vs `_core/include`）。
3. faiss 20180223 版本的 conda 包（从 pytorch/conda-forge channel）是否在 `linux-aarch64` 和 `linux-64` 平台上均可获得？若 conda 安装方式对 arm64 不可用，可能需要保留编译方案并仅修复头文件路径问题。
