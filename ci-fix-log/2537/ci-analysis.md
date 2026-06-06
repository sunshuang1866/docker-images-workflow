# CI 失败分析报告

## 基本信息
- PR: #2537 — Fix: 【自动升级】milvus容器镜像升级至3.0-beta版本.
- 失败类型: infra-error / 证据不足
- 置信度: 低
- 知识库匹配: 模式19 (证据不足)，模式17 (Copyright/SPDX 声明问题) 部分匹配
- 新模式标题: N/A
- 新模式症状关键词: N/A

## 根因分析

### 直接错误
x86-64 和 aarch64 下游构建 job 的实际构建日志**未在提供的 CI 日志中**，仅有 trigger job 的日志。trigger job 本身以 `Finished: SUCCESS` 结束，但两个下游构建 job 均失败：

```
multiarch » openeuler » x86-64 » openeuler-docker-images #1394 completed. Result was FAILURE
multiarch » openeuler » aarch64 » openeuler-docker-images #1369 completed. Result was FAILURE
```

trigger job 中的 Copyright 检查对 PR 涉及的 4 个文件产生 WARNING（非致命错误）：

```
2026-06-06 01:48:41,758 [WARNING] : the copyright in repo is not pass, notice:
openeuler-docker-images/Database/milvus/meta.yml、
openeuler-docker-images/Database/milvus/README.md、
openeuler-docker-images/Database/milvus/3.0-beta/24.03-lts-sp3/Dockerfile、
openeuler-docker-images/Database/milvus/doc/image-info.yml
文件Copyright校验不通过, Copyright path：缺少项目级Copyright声明文件
```

### 根因定位
- 失败位置: 无法定位 — 下游 x86-64 job (#1394) 和 aarch64 job (#1369) 的构建日志均未提供
- 失败原因: **证据不足，无法确定根因**。trigger job 的 license/sca 检查均通过（`check_sca result=0`, `check_package_license result=1`），下游构建的实际失败原因不可见

### 与 PR 变更的关联
- 本 PR (#2537) 是 PR #2529 的修复 PR，目标是为 milvus 3.0-beta 的 4 个文件补 Copyright 和 SPDX 声明
- PR diff 显示已添加 Copyright 头，但版权持有者写为 `Copyright (C) 2026 Zilliz`，SPDX 写为 `SPDX-License-Identifier: Apache-2.0`
- 项目规范（模式17）要求的格式为 `Copyright (c) Huawei Technologies Co., Ltd. 2024-2024. All rights reserved.` + `SPDX-License-Identifier: MulanPSL-2.0`
- **版权持有者和 license 标识均不符合 openEuler 社区规范**，这很可能导致 CI 版权检查未通过
- 此外，历史记录（模式11 中的 PR #2269）表明 milvus `3.0-beta` 条目曾因"包含不稳定版本"被从 `image-info.yml` 移除
- Dockerfile 构建本身可能还存在其他问题（依赖缺失、编译错误等），但因缺少日志无法判断

## 修复方向

### 方向 1（置信度: 中）
将 4 个文件的 Copyright 和 SPDX 声明修改为 openEuler 社区规范格式：
- Dockerfile: `# Copyright (c) Huawei Technologies Co., Ltd. 2024-2024. All rights reserved.` + `# SPDX-License-Identifier: MulanPSL-2.0`
- README.md: `<!-- Copyright (c) Huawei Technologies Co., Ltd. 2024-2024. All rights reserved. -->` + `<!-- SPDX-License-Identifier: MulanPSL-2.0 -->`
- image-info.yml / meta.yml: `# Copyright (c) Huawei Technologies Co., Ltd. 2024-2024. All rights reserved.` + `# SPDX-License-Identifier: MulanPSL-2.0`

### 方向 2（置信度: 低）
Dockerfile 构建本身可能存在运行时错误（依赖安装失败、git clone 超时、编译错误等），但需要获取下游 x86-64/aarch64 构建 job 的完整日志后才能判断。可能的问题点包括：
- `yum install` 中某些包（如 `hdf5`、`hdf5-devel`）在 openEuler 24.03-lts-sp3 仓库中不存在或版本不匹配
- Milvus 3.0-beta 源码编译依赖缺失（参考模式10）
- 网络下载失败（Go、etcd、minio 等上游资源）

### 方向 3（置信度: 低）
参考历史模式11（PR #2269），`3.0-beta` 版本可能被 CI 视为不稳定版本，需从 `image-info.yml` 中移除或调整 CI 版本过滤策略。

## 需要进一步确认的点
1. **下游构建 job 日志缺失**：需要获取 `multiarch/openeuler/x86-64/openeuler-docker-images #1394` 和 `multiarch/openeuler/aarch64/openeuler-docker-images #1369` 的完整构建日志，才能确定 Dockerfile 构建的实际失败原因
2. **Copyright 校验规则**：需确认 openEuler CI 的 Copyright 检查是否强制要求版权持有者为 `Huawei Technologies Co., Ltd.` 和 license 为 `MulanPSL-2.0`，还是允许上游项目保留自身版权和许可证
3. **milvus 3.0-beta 版本状态**：需确认 CI 的版本过滤策略是否允许 `beta` 版本镜像上架，以及 `image-info.yml` 包含测试版是否会被拒绝
4. **Dockerfile 构建可行性**：需在有完整构建环境的条件下验证 Dockerfile 能否成功构建出 milvus 3.0-beta 镜像
