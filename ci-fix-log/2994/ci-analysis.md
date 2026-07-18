# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: goaway, graceful_stop, no builder, rpc error, Unavailable, closing transport, connection error, EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` 安装系统依赖），正在下载 `OS` 仓库元数据时（约 38.59 秒处）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 被 CI 基础设施端主动优雅终止（`goaway: code: NO_ERROR, debug data: "graceful_stop"`），导致正在进行的构建连接断开、builder 实例消失

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个标准结构的 Dockerfile（安装系统包、编译 Python 3.9.19、pip install scann）及配套文档。构建在 `dnf install` 下载仓库元数据的中间阶段被基础设施中断，该阶段尚未执行到任何可能由 Dockerfile 内容引起的错误。`graceful_stop` 的 goaway 信号明确表明是 BuildKit daemon 侧主动终止，属于 CI 基础设施的瞬时问题（如 runner 资源回收、超时、节点伸缩等），与代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。这是 CI 基础设施的瞬时故障（BuildKit builder 被基础设施层终止）。建议直接重新触发 CI 构建。若问题持续复现，需要 CI 运维团队排查 BuildKit builder 的生命周期管理策略（是否有构建超时限制过短、runner 资源不足导致 builder 被驱逐等问题）。

## 需要进一步确认的点

1. 该失败是否为可复现问题（在多次 re-run 中是否都发生），如果仅此一次则为瞬时 infra 故障，无需任何代码修改。
2. 如果多次 re-run 均在同一阶段（`dnf install`）失败，则需排查 CI runner 是否有对单次构建步骤的时间限制，导致 `dnf` 下载大元数据时超时被 kill。
