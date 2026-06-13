# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Conda包版本不可用
- 新模式症状关键词: PackagesNotFoundInChannelsError, not available from current channels, faiss-cpu, conda install

## 根因分析

### 直接错误
```
#8 33.89 PackagesNotFoundInChannelsError: The following packages are not available from current channels:
#8 33.89 
#8 33.89   - faiss-cpu=20180223
#8 33.89 
#8 33.89 Current channels:
#8 33.89 
#8 33.89   - https://conda.anaconda.org/pytorch
#8 33.89   - https://conda.anaconda.org/conda-forge
#8 33.89   - defaults
```

### 根因定位
- 失败位置: `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`:14（`conda install -y -c pytorch -c conda-forge python=3.12 faiss-cpu=20180223`）
- 失败原因: conda 仓库（pytorch、conda-forge、defaults）中不存在 `faiss-cpu=20180223` 这个包版本。该版本对应的 faiss 发布于 2018 年 2 月 23 日，远超 conda-forge 上 faiss-cpu 包的最早收录时间范围，该版本仅能从源码编译安装。

### 与 PR 变更的关联
PR 新增了 `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`，其中 x86_64 架构分支直接尝试通过 `conda install faiss-cpu=20180223` 安装，但该版本在 conda 所有配置的 channel 中均不存在。arm64 分支通过源码编译方式安装（`git clone` + `make`），因此不受此问题影响。**本次失败由 PR 改动直接触发，是 Dockerfile 中安装方式选择错误。**

## 修复方向

### 方向 1（置信度: 高）
将 x86_64 分支的安装方式从 conda 预编译包改为源码编译安装（与 arm64 分支保持一致），使用 `git clone --branch v20180223` + `make` + `python setup.py install` 的流程。注意 x86_64 上编译需要安装对应的系统依赖（如 `openblas-devel`、`gcc-c++` 等），且可能需要移除编译选项中的 x86-only 优化标志（如 `-mavx`、`-msse4`、`-mpopcnt` 等），具体取决于构建环境是否支持这些指令集。

### 方向 2（置信度: 中）
如果 conda-forge 或 pytorch channel 中存在较新但功能兼容的 faiss-cpu 版本（如 `1.7.x`），可考虑改用该版本。但考虑到 PR 明确指定版本为 `20180223`，此方向可能偏离 PR 意图。

## 需要进一步确认的点
- 确认 arm64 源码编译方式在 x86_64 上的可行性，特别是 BLAS 库依赖（mkl vs. openblas）和指令集编译标志的差异处理。
- 确认 CI 构建脚本是否在构建前对 Dockerfile 做了自动化修改（因为日志中 RUN 命令比 PR diff 中的内容更为完整，包含了 arm64/x86_64 分支逻辑，而原始 diff 中仅有一条简单的 `conda install` 指令）。
