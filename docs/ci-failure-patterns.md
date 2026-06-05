# CI 失败模式知识库

本文件由 ci-fix-team 自动维护，记录历史 CI 失败的根因与修复模式，供 AI 分析时参考。


---

## openeuler/openeuler-docker-images PR #2512 · 2026-06-05

| 字段 | 内容 |
|------|------|
| 失败类型 | `无法确定（证据不足）` |
| 置信度 | 低 |

**根因**:
- 失败位置: 无法定位（缺少子任务构建日志）
- 失败原因: 证据不足以确定根因。从上下文推断，失败最可能发生在以下环节之一：Dockerfile 的 RUN 命令执行过程中（编译错误、网络下载失败、命令语法错误），或是 CI 构建环境资源不足（超时、内存溢出）。

**修复方法**:
修复 Dockerfile 中浅克隆（`--depth 1`）与 `git checkout` 指定 commit hash 不兼容的构建逻辑缺陷。

**涉及文件**:
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 在第 23-24 行，将 `git checkout ${VERSION} 2>/dev/null || true` 替换为 `git fetch origin ${VERSION}` + `git checkout ${VERSION}`（移除错误静默掩盖）。


---

## openeuler/openeuler-docker-images PR #2516 · 2026-06-05

| 字段 | 内容 |
|------|------|
| 失败类型 | `无法确定（证据不足）` |
| 置信度 | 低 |

**根因**:
- 失败位置: 无法定位（缺少 `x86-64 » openeuler-docker-images #1361` 的构建日志）
- 失败原因: 下游 x86-64 构建 job 失败，但其详细日志缺失，无法确定根因

**修复方法**:
为 CI `check_package_license` 检查未通过的 4 个新增文件添加 Copyright 声明头（缺失Copyright声明）。

**涉及文件**:
- `AI/vllm-cpu/0.22.1/24.03-lts-sp3/Dockerfile`: 添加 Copyright + SPDX 头
- `AI/vllm-cpu/README.md`: 添加 Copyright + SPDX 头（HTML注释格式）
- `AI/vllm-cpu/doc/image-info.yml`: 添加 Copyright + SPDX 头
- `AI/vllm-cpu/meta.yml`: 添加 Copyright + SPDX 头


---

## openeuler/openeuler-docker-images PR #2516 · 2026-06-05

| 字段 | 内容 |
|------|------|
| 失败类型 | `无法确定（证据不足）` |
| 置信度 | 低 |

**根因**:
- 失败位置: 无法定位（`x86-64 » openeuler-docker-images #1361` 的详细构建日志缺失）
- 失败原因: 下游 x86-64 架构 Docker 镜像构建 job 失败，但提供的日志仅涵盖上游触发 job（SCA 扫描、license 检查），未包含 x86-64 构建 job 的实际执行日志，无法确定具体失败原因。

**修复方法**:
为 PR #2516 涉及的 4 个文件添加缺失的 Copyright 声明头和 SPDX License 标识，解决 CI 中 `check_copyright_in_repo` 警告和 `check_package_license` 未通过的问题。

**涉及文件**:
- `AI/vllm-cpu/0.22.1/24.03-lts-sp3/Dockerfile`: 在文件顶部添加 Copyright + SPDX 两行注释头
- `AI/vllm-cpu/README.md`: 在文件顶部添加 Copyright + SPDX 的 HTML 注释块
- `AI/vllm-cpu/doc/image-info.yml`: 在文件顶部添加 Copyright + SPDX 两行注释头
- `AI/vllm-cpu/meta.yml`: 在文件顶部添加 Copyright + SPDX 两行注释头

