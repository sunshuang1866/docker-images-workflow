# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 异常终止
- 新模式症状关键词: `graceful_stop`, `no builder found`, `closing transport`, `rpc error`, `connection error`

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `#7 [2/4] RUN dnf install -y ...`
- 失败原因: BuildKit Docker 构建器 `euler_builder_20260709_224657` 在构建过程中被异常终止（gRPC goaway 附带 `graceful_stop` 标志），导致所有正在运行的构建步骤被中断，后续无法再找到该 builder

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个标准的 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）和配套的元数据文件更新。构建在前 6 步（拉取基础镜像、加载 Dockerfile、下载 .dockerignore）均成功完成，在步骤 `#7` 执行 `dnf install` 下载软件包元数据时，BuildKit builder 进程被外部终止。该 Dockerfile 内容和结构与其他已成功的同类 Dockerfile 一致，不存在语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 高）
这是一个 CI 基础设施故障（BuildKit builder 进程意外终止），与 PR 代码变更无关，**无需修改任何代码**。Code Fixer 无需处理。建议重新触发 CI 运行，构建器可恢复后构建预期可正常通过。

## 需要进一步确认的点
- 该 BuildKit builder (`euler_builder_20260709_224657`) 被 `graceful_stop` 的原因（可能是  CI 节点的资源限制、Docker daemon 重启、或调度层面的主动回收）
- 重新触发 CI 后是否复现——若持续复现，可能存在 builder 资源分配或超时配置问题而非本次 PR 引入
