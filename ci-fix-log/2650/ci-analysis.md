# CI 失败分析报告

## 基本信息
- PR: #2650 — 【自动升级】torchvision容器镜像升级至0.27.1版本.
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: PyTorch版本锁定冲突
- 新模式症状关键词: ResolutionImpossible, conflicting dependencies, torchvision depends on torch

## 根因分析

### 直接错误
```
#8 11.81 ERROR: Cannot install torch==2.12.0 and torchvision==0.27.1+cpu because these package versions have conflicting dependencies.
#8 11.81
#8 11.81 The conflict is caused by:
#8 11.81     The user requested torch==2.12.0
#8 11.81     torchvision 0.27.1+cpu depends on torch==2.12.1
#8 11.81
#8 11.81 ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
#8 ERROR: process "/bin/sh -c pip install --no-cache-dir         --index-url https://download.pytorch.org/whl/cpu         torch==${TORCH_VERSION}         torchvision==${VERSION}" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `AI/torchvision/0.27.1/24.03-lts-sp3/Dockerfile`:10（pip install 步骤）
- 失败原因: Dockerfile 中 `TORCH_VERSION=2.12.0` 与 torchvision 0.27.1 的上游依赖 `torch==2.12.1` 不兼容，pip 依赖解析器无法满足约束。

### 与 PR 变更的关联
本次 PR 新增了 `AI/torchvision/0.27.1/24.03-lts-sp3/Dockerfile`（新文件，13 行全新增），其中 `ARG TORCH_VERSION=2.12.0` 硬编码了一个错误的 torch 版本。该错误版本号是自动升级脚本根据某种规则推算得出的（或沿用了旧版本 Dockerfile 的模板），但实际上 torchvision 0.27.1 在 PyTorch CPU wheel 索引中依赖 `torch==2.12.1`。此问题完全由本次 PR 引入。

## 修复方向

### 方向 1（置信度: 高）
将 `ARG TORCH_VERSION=2.12.0` 修正为 `ARG TORCH_VERSION=2.12.1`，以匹配 torchvision 0.27.1 的上游依赖要求。

### 方向 2（置信度: 中）
若上游实际有多个可用的 torch 版本能满足 torchvision 0.27.1，可考虑去掉 `torch==${TORCH_VERSION}` 的精确版本约束，让 pip 自行解析。但从日志中 pip 已尝试解析多个版本仍失败来看（`pip is looking at multiple versions of torchvision to determine which version is compatible`），方向 1 是最直接的方案。

## 需要进一步确认的点
- 确认 torchvision 0.27.1 在 `https://download.pytorch.org/whl/cpu` 上是否确实只兼容 torch 2.12.1，以及 torch 2.12.1 是否在该索引中存在。
- 确认自动升级脚本生成 TORCH_VERSION 的逻辑是否需要修正，避免后续版本升级时再次硬编码错误的依赖版本。
