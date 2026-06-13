# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 源码构建路径错误
- 新模式症状关键词: No such file or directory, setup.py, faiss, python

## 根因分析

### 直接错误
```
#8 138.5 python: can't open file '/tmp/faiss-20180223/python/setup.py': [Errno 2] No such file or directory
#8 ERROR: process "/bin/sh -c conda tos accept ... && cd python && python setup.py install ..." did not complete successfully: exit code: 2
------
Dockerfile:14
```

### 根因定位
- 失败位置: `AI/faiss/20180223/24.03-lts-sp3/Dockerfile:14`（第2个 RUN 命令中 `cd python && python setup.py install` 这一步）
- 失败原因: faiss 20180223 是 2018 年的早期版本，其源码 `python/` 目录下不存在 `setup.py` 文件。C++ 库（`libfaiss.a`）编译成功，但 Python 绑定安装步骤因目标文件缺失而失败。

### 与 PR 变更的关联
本次 PR 新增了 faiss 20180223 的 Dockerfile。CI 构建日志中实际执行的 RUN 命令内容（conda 安装 python+numpy + dnf 安装编译工具 + 从源码编译 faiss + `python setup.py install`）与 PR diff 中展示的 Dockerfile（conda 直接安装 faiss-cpu 预编译包）存在明显差异。无论以哪个版本的 Dockerfile 为准，错误均发生在构建流程的 Python 安装阶段。若以 CI 实际执行的逻辑为准，问题直接源于 Dockerfile 对 faiss 老版本源码结构的假设错误。

## 修复方向

### 方向 1（置信度: 高）
faiss 20180223 的 `python/` 目录不包含 `setup.py`。需确认该版本实际的 Python 绑定构建方式：
- 若该目录下有 `Makefile`，改用 `make -C python install`
- 若该版本通过 SWIG 生成绑定，需先 `make swig` 再安装
- 若该版本根本没有 Python 绑定，移除 `cd python && python setup.py install` 步骤

### 方向 2（置信度: 中）
改用 conda 从 pytorch/conda-forge channel 直接安装 faiss-cpu 预编译包，避免源码编译。但需先确认 `faiss-cpu=20180223` 在 conda 仓库中是否可用——早期版本可能未被收录。

## 需要进一步确认的点
1. faiss v20180223 源码 `python/` 目录的实际内容（`Makefile` / `setup.py` / 空目录）
2. CI 实际构建的 Dockerfile 是否与 PR diff 一致——日志中的 RUN 命令比 diff 多出大量源码编译步骤
3. 若 CI 实际执行的 Dockerfile 与 diff 不同，需确认来源（是否被其他提交覆盖或 CI 使用了错误版本的 Dockerfile）
