# CI 失败分析报告

## 基本信息
- PR: #2529 — 【自动升级】milvus容器镜像升级至3.0-beta版本.
- 失败类型: infra-error / lint-error
- 置信度: 中
- 知识库匹配: 模式17、模式11、模式20
- 新模式标题: —
- 新模式症状关键词: —

## 根因分析

### 直接错误

**错误 1 — Copyright 校验失败（trigger job 中可确认）:**

```
2026-06-06 00:40:02,608 [WARNING] : the copyright in repo is not pass, notice:
  openeuler-docker-images/Database/milvus/README.md、
  openeuler-docker-images/Database/milvus/doc/image-info.yml
  文件Copyright校验不通过,
  openeuler-docker-images/Database/milvus/meta.yml、
  openeuler-docker-images/Database/milvus/3.0-beta/24.03-lts-sp3/Dockerfile
  文件缺失Copyright声明,
  Copyright path：缺少项目级Copyright声明文件

check result: ACL=[{"name": "check_sca", "result": 0}, {"name": "check_package_license", "result": 1}]
```

**错误 2 — 下游构建失败（日志缺失）:**

```
multiarch » openeuler » x86-64 » openeuler-docker-images #1386 completed. Result was FAILURE
multiarch » openeuler » aarch64 » openeuler-docker-images #1361 completed. Result was FAILURE
```

### 根因定位

本次 CI 失败包含两个层面的问题：

1. **Copyright/SPDX 声明缺失（模式17）**— 已确认
   - 失败位置: `Database/milvus/3.0-beta/24.03-lts-sp3/Dockerfile`、`Database/milvus/README.md`、`Database/milvus/doc/image-info.yml`、`Database/milvus/meta.yml`
   - 失败原因: PR 新增/修改的 4 个文件均未包含 Copyright 声明和 SPDX-License-Identifier 头，且缺少项目级 Copyright 声明文件，导致 `check_package_license` 检查未通过（result=1）。

2. **x86-64 与 aarch64 下游构建失败（模式20）**— 证据不足
   - 失败位置: 无法定位（下游构建 job 日志未提供）
   - 失败原因: 证据不足，无法确定根因。需要获取 x86-64 job #1386 和 aarch64 job #1361 的实际构建日志才能进一步分析。

3. **历史预警 — image-info.yml 包含 beta 版本（模式11）**— 间接相关
   - 历史案例 PR #2269 显示，`Database/milvus/doc/image-info.yml` 中曾因包含不稳定 `3.0-beta` 版本条目导致 CI 失败。当前 PR 正在向同一文件添加 `3.0-beta-oe2403sp3` 条目，存在同类风险。

### 与 PR 变更的关联

- **直接关联**: PR 新增了 `Database/milvus/3.0-beta/24.03-lts-sp3/Dockerfile`（全新文件），并修改了 `Database/milvus/README.md`、`Database/milvus/doc/image-info.yml`、`Database/milvus/meta.yml` 三个文件。这 4 个文件均缺少 Copyright + SPDX 声明头，触发了 CI 的 `check_package_license` 检查失败（模式17）。
- **潜在关联**: PR 向 `image-info.yml` 添加的是 `3.0-beta` 版本条目，而历史模式11（PR #2269）明确记录了 milvus 的 beta 版本条目被标记为不稳定并需移除。这可能也是下游构建失败的诱因之一，但缺少日志无法确认。
- **下游构建失败与 PR 的关联无法判断**: 缺少 x86-64 和 aarch64 构建日志。

## 修复方向

### 方向 1（置信度: 高）— 补充 Copyright + SPDX 声明头

为 PR 涉及的全部 4 个文件添加格式正确的 Copyright 和 SPDX-License-Identifier 头，并为项目级补充 Copyright 声明文件。参考模式17中定义的各文件类型模板格式。

### 方向 2（置信度: 中）— 评估 3.0-beta 版本是否应出现在 image-info.yml

历史模式11（PR #2269）显示 milvus `3.0-beta` 被认定为不稳定版本，不应出现在 `image-info.yml` 中。需确认当前项目规范是否允许 beta 版本录入该文件。若不允许，应从 `image-info.yml` 和 `README.md` 的表格中移除该条目。

### 方向 3（置信度: 低）— 获取下游构建日志后分析实际构建失败

x86-64 和 aarch64 构建均失败，但无日志。需获取 job #1386 和 #1361 的完整构建日志，排查是否存在编译错误（如 cmake 缺少依赖 → 模式10）、网络下载错误（404 → 模式01/02/03）、或其他运行时错误。

## 需要进一步确认的点

1. **下游构建日志缺失**：x86-64 job #1386 和 aarch64 job #1361 的实际构建日志未提供，无法判断构建阶段的失败是 Dockerfile 问题还是基础设施问题。这是当前最大的信息缺口。
2. **`check_package_license` 是否为阻塞项**：需确认 trigger job 中 `check_package_license` 结果为 1 时是否会直接阻止下游构建 job 启动，还是仅作为警告继续触发下游构建。
3. **3.0-beta 版本准入策略**：需向项目维护者确认 `image-info.yml` 是否允许收录 beta/预发布版本条目。历史模式11 显示此前被拒绝。
4. **Dockerfile 本身的可构建性**：新 Dockerfile 中硬编码了 `GOLANG_VERSION=1.24.2`、`conan==1.61.0`、`etcd-v3.5.0` 等版本号，需确认这些版本在 CI 构建时均可正常下载和安装。
