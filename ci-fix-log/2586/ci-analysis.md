# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 旧版源码缺setup.py
- 新模式症状关键词: No such file or directory, setup.py, python, faiss, 20180223

## 根因分析

### 直接错误
```
#8 138.5 python: can't open file '/tmp/faiss-20180223/python/setup.py': [Errno 2] No such file or directory
#8 ERROR: process "/bin/sh -c conda tos accept ... dnf install -y gcc-c++ make openblas-devel && ... curl -fSL .../faiss/archive/v${VERSION}.tar.gz && ... make -j$(nproc) && cd python && python setup.py install ..." did not complete successfully: exit code: 2
------
Dockerfile:14
```

### 根因定位
- 失败位置: `AI/faiss/20180223/24.03-lts-sp3/Dockerfile:14`（`RUN` 指令中 `cd python && python setup.py install` 步骤）
- 失败原因: faiss 20180223 是 2018 年的历史版本，其源代码目录中**不包含 `python/setup.py` 文件**。CI 实际执行的 Dockerfile 试图从 GitHub 下载源码后运行 `make` 编译 C++ 库，再通过 `cd python && python setup.py install` 安装 Python 绑定，但该旧版本中 `python/` 目录下不存在 `setup.py`，导致 Python 模块安装步骤失败（exit code: 2）。

### 与 PR 变更的关联
**存在关键不一致**：PR diff 中的 Dockerfile 使用 `conda install -c pytorch -c conda-forge python=3.12 faiss-cpu=${VERSION}` 从 conda 仓库安装预编译包（纯 conda 方式，无源码编译步骤），而 CI 日志中实际执行的 Dockerfile 采用了完全不同的构建路径——通过 `dnf install gcc-c++ make openblas-devel`、`curl` 下载源码、`make` 编译 C++、再 `python setup.py install` 安装 Python 绑定（源码编译方式）。CI 构建的 Dockerfile 内容与 PR diff 不匹配。

此外，日志中编译阶段（`make -j$(nproc)`）和静态库打包（`ar r libfaiss.a ...`）均成功完成，仅有若干无害的 C++ 编译器 warning，失败仅发生在最后的 Python 安装步骤。

## 修复方向

### 方向 1（置信度: 高）
确认 CI 构建是否使用了正确的代码版本。PR diff 意图使用 conda 一键安装预编译的 `faiss-cpu` 包，无需源码编译。如果 CI 正确执行 PR diff 中的 Dockerfile，则不应出现此错误。需排查 CI 流水线是否拉取了错误的代码分支/提交。

### 方向 2（置信度: 中）
如果确实需要保留源码编译方式，需针对 faiss 20180223 版本调整 Python 绑定安装步骤。faiss 20180223 的 Python 模块可能通过 Makefile 直接编译安装（使用 `make -C python` 或 `python setup.py build` 的不同变体），而非现代版的 `pip install .` / `python setup.py install`。需查阅 faiss 20180223 源码中 `python/` 目录下实际的构建方式（如是否存在 `Makefile`，或需使用 `swig` 等方式）。

### 方向 3（置信度: 低）
如果 conda-forge / pytorch channel 不提供 `faiss-cpu=20180223` 的预编译包，可考虑将 PR diff 中的 conda 安装方式与源码编译方式结合：保留 `make` 编译 C++ 库，但用 `pip install .` 替换 `python setup.py install`（如果该版本 `python/` 目录下有 `pyproject.toml` 或兼容的打包文件），或改用 `make -C python` 根据该版本的 Makefile 规则安装。

## 需要进一步确认的点
1. CI 日志中执行的 Dockerfile（源码编译方式）与 PR diff 中的 Dockerfile（conda 安装方式）完全不一致，需确认 CI 是否使用了正确的代码。可能当前 CI 构建的 Dockerfile 是另一个版本或尚未被 PR diff 替换的旧版本。
2. faiss 20180223 源码（`https://github.com/facebookresearch/faiss/archive/v20180223.tar.gz`）中 `python/` 目录的实际文件列表，确认该版本 Python 绑定的真实构建方式。
3. conda-forge / pytorch channel 中是否存在 `faiss-cpu=20180223` 版本——若无，则 PR diff 中的纯 conda 方案本身也可能失败，需综合评估。
