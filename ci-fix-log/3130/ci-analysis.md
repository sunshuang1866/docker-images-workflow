# CI 失败分析报告

## 基本信息
- PR: #3130 — chore(llm): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式30
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#10 0.070 exec /bin/sh: exec format error
#10 ERROR: process "/bin/sh -c chmod +x /demo/*.sh && ..." did not complete successfully: exit code: 255
------
 - InvalidBaseImagePlatform: Base image ****/llm:fastchat-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2 was pulled with platform "linux/arm64", expected "linux/amd64" for current build (line 1)
ERROR: failed to solve: process "/bin/sh -c chmod +x /demo/*.sh && ..." did not complete successfully: exit code: 255
```

### 根因定位
- 失败位置: `AI/llm/chatglm2_6b-pytorch2.1.0.a1-cann7.0.RC1.alpha002/24.03-lts-sp4/Dockerfile:1`
- 失败原因: 新增的 Dockerfile 以 `FROM openeuler/llm:fastchat-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2` 为基础镜像，该镜像仅存在于 `linux/arm64` 架构。CI 在 x86_64 构建节点（`ecs-build-docker-x86-hk`）上拉取到 arm64 版本的镜像，导致 `/bin/sh` 因架构不匹配而报 `exec format error`。
- 直接诱因: `meta.yml` 中新增的 `chatglm2_6b-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2403sp4` 条目缺少 `arch: aarch64` 约束，CI 调度器未将其限制在 aarch64 节点上构建。

### 与 PR 变更的关联
PR 新增了 `24.03-lts-sp4` 版本的 chatglm2_6b Dockerfile，该 Dockerfile 复用了 `oe2203sp2` 的 base image（仅 arm64 可用）。同时 `meta.yml` 新增了对应的镜像条目，但未添加 `arch` 字段限制构建架构。这是本次 PR 直接引入的问题。

## 修复方向

### 方向 1（置信度: 高）
在 `AI/llm/meta.yml` 中为新增的 `chatglm2_6b-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2403sp4` 条目添加 `arch: aarch64` 约束，与模式30/31同理，确保 CI 仅将构建调度到 aarch64 节点。同时需检查已有的 `chatglm2_6b-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2` 条目是否也存在同样的缺省 `arch` 问题，一并进行修复。

### 方向 2（置信度: 低）
若 `fastchat-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2` 实际上存在 x86_64 版本，则需排查 BuildKit 为何拉取了错误的平台清单（可能的 docker buildx 平台参数未正确指定）。但 CI 日志中的 `InvalidBaseImagePlatform` 警告更倾向于该镜像确实仅有 arm64 版本。

## 需要进一步确认的点
- 确认 `fastchat-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2` 在容器镜像仓库中是否同时发布有 `linux/amd64` 和 `linux/arm64` 两个平台的 manifest。若仅有 arm64，则 `arch: aarch64` 是必需的。
- 确认已有的 `chatglm2_6b-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2` 条目是否已在其他 CI pipeline 中正确配置架构限制（或被排外到仅 aarch64 流水线）。
