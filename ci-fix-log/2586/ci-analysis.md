# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: numpy头文件缺失
- 新模式症状关键词: numpy/arrayobject.h, No such file or directory, make py, swigfaiss

## 根因分析

### 直接错误
```
#8 724.0 python/swigfaiss_wrap.cxx:3228:10: fatal error: numpy/arrayobject.h: No such file or directory
#8 724.0  3228 | #include <numpy/arrayobject.h>
#8 724.0       |          ^~~~~~~~~~~~~~~~~~~~~
#8 724.0 compilation terminated.
#8 724.1 make: *** [Makefile:84: python/_swigfaiss.so] Error 1
#8 ERROR: process "/bin/sh -c ... make py ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: python/swigfaiss_wrap.cxx:3228；对应 Dockerfile 中第 14 行起的大段 RUN 指令内的 `make py` 步骤
- 失败原因: faiss C++ 源码构建阶段，`make py` 编译 Python SWIG 绑定时，编译器无法找到 `numpy/arrayobject.h` 头文件。虽然 RUN 命令开头通过 `conda install -y python=3.12 numpy` 安装了 numpy，且 `make py` 的 PYTHONCFLAGS 中指定了 `-I/opt/conda/lib/python3.12/site-packages/numpy/core/include`，但该路径下不存在编译器所需的 `numpy/arrayobject.h`，导致 SWIG 包装代码编译失败。

### 与 PR 变更的关联

**关键发现——PR diff 与 CI 实际执行的 Dockerfile 存在重大差异**：

- PR diff 中的 Dockerfile 仅有 21 行，核心安装逻辑为：`conda install -y -c pytorch -c conda-forge python=3.12 faiss-cpu=${VERSION}`，即通过 conda 安装**预编译**的 faiss-cpu 包，完全不需要从源码编译。
- CI 实际执行的 Dockerfile 采用**从源码编译 faiss** 的方式（`make -j$(nproc)` + `make py`），包含 dnf 安装 gcc-c++/make/openblas-devel/swig 等编译依赖、从 GitHub 下载 faiss 源码并编译的完整过程。

由于 CI 运行的是一个与 PR diff 不同（且更复杂）的 Dockerfile，无法确认 PR 所提交的 conda 安装方案是否能正常通过构建。**本次失败不是 PR diff 中的代码直接导致的，而是 CI 执行了另一份含源码编译逻辑的 Dockerfile 所致。**

## 修复方向

### 方向 1（置信度: 中）
若 CI 期望的方案确为源码编译（即 CI 执行的 Dockerfile 是正确的基准），则需要修复 numpy 头文件路径：`conda install` 安装的 numpy 在 `/opt/conda/lib/python3.12/site-packages/numpy/core/include/` 下可能缺少 `numpy/arrayobject.h`，需指定正确的 include 路径，或确认 numpy 版本是否完整携带 C 头文件（`numpy.get_include()` 返回的实际路径）。

### 方向 2（置信度: 中）
若 PR diff 中的 conda 安装方案才是正确目标（即应使用预编译 faiss-cpu 绕过编译），则 CI 流水线未正确拉取该 Dockerfile，需检查 CI 是否使用了错误的 Dockerfile 路径/版本，确保 CI 构建的是 PR 中实际提交的 Dockerfile。

## 需要进一步确认的点
1. **CI 流水线配置**：CI 实际拉取的 Dockerfile 源路径是什么？是否与 PR diff 中的 `AI/faiss/20180223/24.03-lts-sp3/Dockerfile` 一致？若不匹配，需检查 CI pipeline 的 Dockerfile 选取逻辑。
2. **numpy 头文件位置**：在 CI 构建容器内实际检查 `python -c "import numpy; print(numpy.get_include())"` 的输出，确认 numpy 头文件的实际安装路径，以判断 `-I` 参数是否指向了错误位置。
3. **faiss-cpu conda 包可用性**：确认 `conda install -y -c pytorch -c conda-forge python=3.12 faiss-cpu=20180223` 是否能在目标频道（pytorch / conda-forge）正常解析和安装，验证 PR diff 方案的可行性。
4. **本次是否为自动升级生成脚本的产物**：PR 标题含"自动升级"，若 Dockerfile 由脚本根据模板生成，需检查生成脚本是否存在 bug 导致输出了错误的 Dockerfile 内容。
