# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本.
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Conda包版本不存在
- 新模式症状关键词: PackagesNotFoundInChannelsError, faiss-cpu, conda install, not available from current channels

## 根因分析

### 直接错误
```
#8 35.72 PackagesNotFoundInChannelsError: The following packages are not available from current channels:
#8 35.72
#8 35.72   - faiss-cpu=20180223
#8 35.72
#8 35.72 Current channels:
#8 35.72
#8 35.72   - https://conda.anaconda.org/pytorch
#8 35.72   - https://conda.anaconda.org/conda-forge
#8 35.72   - defaults
#8 35.72
#8 35.72 To search for alternate channels that may provide the conda package you're
#8 35.72 looking for, navigate to
#8 35.72
#8 35.72     https://anaconda.org
#8 ERROR: process "/bin/sh -c conda tos accept ... && conda install -y -c pytorch -c conda-forge python=3.12 faiss-cpu=${VERSION} && conda clean -afy" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`:14-17（conda install 步骤）
- 失败原因: conda 的 pytorch / conda-forge / defaults 三个 channel 中均不存在 `faiss-cpu` 版本 `20180223`。`20180223` 是 FAISS 上游的日期式版本号（如 2018-02-23），而 conda channel 中提供的 `faiss-cpu` 包使用语义化版本（如 1.7.4、1.14.1 等），两者不匹配。

### 与 PR 变更的关联
PR 新增了 `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`，其中 `Dockerfile:9` 定义 `ARG VERSION=20180223`，并在 `Dockerfile:16` 的 `conda install` 命令中引用 `faiss-cpu=${VERSION}`。该版本号在 conda 的任意 channel 中均不可用，属于 PR 自身引入的问题。自动升级脚本使用了上游仓库的 tag 名称（20180223）作为版本号，但该 tag 名称并非 conda 包的实际版本标识。

## 修复方向

### 方向 1（置信度: 高）
将 `faiss-cpu` 的 conda 安装版本号从 `20180223` 改为 conda channel 中实际存在的对应版本。需要到 https://anaconda.org 搜索 `faiss-cpu`，确认与上游 FAISS 20180223 对应的 conda 包版本号（或最接近的可用版本），然后更新 `meta.yml` 中的 tag 名称和 Dockerfile 中的 VERSION 参数。

### 方向 2（置信度: 中）
如果 conda 中确实没有 FAISS 20180223 对应的包，可改用 pip 安装：`pip install faiss-cpu==<对应 PyPI 版本号>`，或从源码编译安装。PyPI 上 faiss-cpu 的版本命名可能同样不含 `20180223` 字面值，需查证。

## 需要进一步确认的点
- FAISS 上游 tag `20180223` 对应的实际语义化版本号是多少（如在 PyPI 或 conda-forge 上对应的版本标识）
- conda-forge 上 `faiss-cpu` 包是否收录过该早期版本，若未收录则需要改用 pip 安装或源码编译
- 同仓库中已存在的 `faiss/1.14.1/24.03-lts-sp3/Dockerfile` 同样使用 conda 安装且版本号 `1.14.1` 可正常工作，可作为版本号格式的参照
