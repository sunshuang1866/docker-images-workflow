# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: numpy头文件缺失
- 新模式症状关键词: `numpy/arrayobject.h: No such file or directory`, `fatal error`, `make py`, `swigfaiss_wrap.cxx`

## 根因分析

### ⚠️ 前置发现：PR diff 与 CI 实际执行的 Dockerfile 不一致

PR diff 中的 Dockerfile（21 行）使用 `conda install -y -c pytorch -c conda-forge python=3.12 faiss-cpu=${VERSION}` 直接安装预编译的 faiss-cpu conda 包，**不需要从源码编译**。

但 CI 日志中实际执行的 Dockerfile 是一个不同的版本，它在 `Dockerfile:14` 处包含一个从源码编译 faiss 的 RUN 命令（包括 `conda install numpy`、`dnf install` 编译工具链、`curl` 下载源码、`make`、`make py` 等步骤）。这两个 Dockerfile 的内容和行号结构完全不同。

需进一步确认 CI 系统是否对 PR 提交的 Dockerfile 做了自动转化/包装，或 CI 流水线使用的 Dockerfile 来源是否与 PR diff 一致。

### 直接错误
```
724.0 g++ -I. -fPIC -m64 -Wall -g -O3 -mavx -msse4 -mpopcnt -fopenmp -Wno-sign-compare \
  -std=c++11 -fopenmp -g -fPIC -fopenmp \
  -I/opt/conda/include/python3.12 \
  -I/opt/conda/lib/python3.12/site-packages/numpy/core/include -shared \
  -o python/_swigfaiss.so python/swigfaiss_wrap.cxx libfaiss.a /usr/lib64/libopenblas.so.0
724.0 python/swigfaiss_wrap.cxx:3228:10: fatal error: numpy/arrayobject.h: No such file or directory
724.0  3228 | #include <numpy/arrayobject.h>
724.0       |          ^~~~~~~~~~~~~~~~~~~~~
724.0 compilation terminated.
724.1 make: *** [Makefile:84: python/_swigfaiss.so] Error 1
```

### 根因定位
- 失败位置: `make py` 步骤 — 编译 `python/swigfaiss_wrap.cxx:3228`
- 失败原因: `make py` 通过 `PYTHONCFLAGS` 指定的 numpy include 路径 (`-I/opt/conda/lib/python3.12/site-packages/numpy/core/include`) 下不存在 `numpy/arrayobject.h`，导致 SWIG 生成的 Python 绑定 C++ 文件编译失败

### 与 PR 变更的关联

PR 新增了 `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`。该 Dockerfile 使用 conda 预编译包安装 faiss-cpu，不应触发源码编译。但 CI 实际执行了一个从源码构建 faiss 的 Dockerfile（与 PR diff 不匹配），该构建流程中 `make py` 阶段因 numpy 头文件路径问题失败。

**直接关联性**：中等。即使 PR 的 Dockerfile 是设计意图，CI 流水线的实际执行路径与之不一致，需先确认这种不一致是否为 CI 系统的预期行为（如 CI 自动将 conda 安装转化为源码编译）。

## 修复方向

### 方向 1（置信度: 中）
如果 CI 系统对 Dockerfile 有自动转化逻辑（将 conda 安装替换为源码编译），则需在 CI 转化的 Dockerfile 中，将 `make py` 的 `PYTHONCFLAGS` 中的 numpy include 路径修正为 conda 环境下 numpy 头文件的实际位置。

conda 安装的 numpy 头文件可能位于：
- `site-packages/numpy/core/include/numpy/`（旧版 numpy 1.x）
- `site-packages/numpy/_core/include/numpy/`（numpy 2.x）
- conda 环境的 `include/` 目录（如 `/opt/conda/include/python3.12/numpy/`）

需在 CI 转化逻辑中，通过 `python -c "import numpy; print(numpy.get_include())"` 动态获取 numpy 头文件实际位置，替代硬编码路径。

### 方向 2（置信度: 低）
如果 PR diff 中的 Dockerfile 就是最终目标，且 CI 只是使用了错误的 Dockerfile 版本进行测试，则无需修改 Dockerfile，只需确保 CI 使用正确的 Dockerfile（即直接通过 conda 安装 faiss-cpu 而非从源码编译）重新触发构建即可。

## 需要进一步确认的点
1. CI 系统是否对提交的 Dockerfile 存在自动包装/转化机制——PR diff 中仅 21 行的 conda 安装 Dockerfile 为何在 CI 中变成了 ~28 行、包含完整源码编译流程的 Dockerfile？
2. 如果 CI 转化是预期行为，需确认 conda 环境下 `python -c "import numpy; print(numpy.get_include())"` 的实际输出路径，以验证当前 `PYTHONCFLAGS` 中的硬编码路径是否正确
3. faiss 20180223 是否需要 numpy 2.x 的兼容性补丁（SWIG 生成的代码期望旧版 numpy 头文件结构）？
4. 同一镜像的 `1.14.1` 版本（`AI/faiss/1.14.1/24.03-lts-sp3/Dockerfile`）是否也使用了相同的 CI 编译流水线？如果该版本构建成功，可对比其 numpy 头文件路径处理方式
