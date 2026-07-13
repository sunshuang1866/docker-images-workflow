# CI 失败分析报告

## 基本信息
- PR: #3130 — chore(llm): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 平台架构不匹配
- 新模式症状关键词: exec format error, InvalidBaseImagePlatform, arm64, amd64, platform mismatch

## 根因分析

### 直接错误
```
#10 0.070 exec /bin/sh: exec format error
#10 ERROR: process "/bin/sh -c chmod +x /demo/*.sh &&     git clone https://huggingface.co/THUDM/chatglm2-6b &&     cd chatglm2-6b &&     git apply ../chatglm2-6b.patch" did not complete successfully: exit code: 255

 InvalidBaseImagePlatform: Base image ***/llm:fastchat-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2 was pulled with platform "linux/arm64", expected "linux/amd64" for current build (line 1)
```

### 根因定位
- 失败位置: `AI/llm/chatglm2_6b-pytorch2.1.0.a1-cann7.0.RC1.alpha002/24.03-lts-sp4/Dockerfile:1`（FROM 指令）
- 失败原因: CI 在 x86_64 构建节点（`ecs-build-docker-x86-hk`）上执行构建，但基础镜像 `openeuler/llm:fastchat-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2` 仅提供 `linux/arm64` 平台的 manifest，不存在 `linux/amd64` 变体。Docker 在 x86_64 宿主机上拉取了 arm64 镜像后，执行 `/bin/sh` 时触发 `exec format error`（CPU 架构与二进制不兼容）。

### 与 PR 变更的关联
**PR 变更本身无问题**。PR 新增的 Dockerfile 正确复用了已有的基础镜像标签 `fastchat-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2`（与现有 22.03-lts-sp2 版本共用同一 FROM 行），代码逻辑无错误。失败根因为 CI 基础设施层面：该基础镜像（CANN/Ascend NPU 加速器专用）可能本身只支持 aarch64 架构，而 CI 的 x86-64 构建流水线未能跳过此镜像的构建。

## 修复方向

### 方向 1（置信度: 高）
确认该镜像是否需要支持 x86_64 架构构建。如果该 LLM 应用镜像依赖 Ascend NPU 硬件且仅在 aarch64 上可用，应在 CI 流水线层面为该 Dockerfile 的 `meta.yml` 条目添加构建架构限制（仅触发 aarch64 builder），或在元数据中标记为 aarch64-only。PR 代码无需修改。

### 方向 2（置信度: 中）
如果确实需要 x86_64 构建支持，需要为基础镜像 `openeuler/llm:fastchat-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2` 补充 amd64 manifests（即构建并推送该镜像的 x86_64 版本到 registry）。

## 需要进一步确认的点
1. 基础镜像 `openeuler/llm:fastchat-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2` 是否有 amd64 版本？需要查询 Docker Hub 上该 tag 的 multi-arch manifest 列表
2. 现有 22.03-lts-sp2 版本的 `chatglm2_6b` 镜像在 CI 中是如何通过 x86-64 构建的？是否之前也是同样问题被忽略或跳过？
3. CI 流水线是否支持为不同镜像指定目标构建架构（multiarch build matrix）？
