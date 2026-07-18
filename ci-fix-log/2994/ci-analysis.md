# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 连接断开
- 新模式症状关键词: closing transport, no builder found, goaway, graceful_stop, euler_builder, rpc error

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建步骤 #7（`dnf install` 阶段），非 PR 代码文件
- 失败原因: Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 下载系统包元数据时被优雅关闭（`graceful_stop`），gRPC 连接断开，构建客户端无法继续接收构建状态，构建被标记为失败。这是 CI 基础设施层面的问题（builder 节点被终止/重启/回收），与 PR 代码变更无关。

### 与 PR 变更的关联
PR 仅新增了一个 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）及配套的元数据/文档更新。构建失败发生在 `dnf install` 安装基础系统包的阶段（步骤 #7 的元数据下载过程中），尚未进入任何 PR 特定的构建逻辑。该错误完全由 CI 基础设施（BuildKit builder 实例异常退出）导致，与 PR 变更无关。

## 修复方向

### 方向 1（置信度: 高）
无需修复 PR 代码。该失败是 CI 基础设施的 Builder 节点不稳定所致，建议 **重试 CI 流水线**，或联系 CI 运维团队排查 `ecs-build-docker-x86-hk` 节点上 BuildKit builder 实例的稳定性（是否因资源不足、OOM 或定时回收策略导致 `graceful_stop`）。

## 需要进一步确认的点
- `euler_builder_20260709_224657` builder 实例为何被 graceful stop：是人工操作、节点资源配额限制、OOM Killer 触发，还是 CI 调度系统的自动回收机制
- 该 builder 节点近期是否频繁出现同类 builder 断连问题（若频繁出现则需 CI 运维介入）

## 修复验证要求
无需验证，该失败属于 infra-error，不涉及对代码、Dockerfile 或正则匹配的任何修改。
