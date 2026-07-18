# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 连接中断
- 新模式症状关键词: `graceful_stop`, `no builder`, `closing transport`, `rpc error`, `code = Unavailable`

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`（Dockerfile 第 8 行附近）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在执行构建过程中被服务端主动终止（`graceful_stop`），导致客户端 gRPC 连接断开（`closing transport` + `EOF`），后续尝试查找该 builder 时已不存在（`no builder ... found`）

### 与 PR 变更的关联
- **与 PR 变更无关**。该失败是 CI 基础设施（BuildKit 服务端）自身的 builder 回收/重启行为导致。
- Docker 构建仅在步骤 `[2/4]`（`dnf install` 下载元数据阶段，进度约 39 秒、速率 77 kB/s）时 builder 即被终止，步骤远未执行到 `pip install scann` 等软件特有逻辑。
- CI 预检阶段（镜像规范检查、Git 克隆）全部通过，未报告任何 PR 代码层面的错误。
- 日志中 `graceful_stop` 和 `NO_ERROR` 明确表明 builder 端为主动、无错误的关闭，属于基础设施生命周期管理范畴，非构建逻辑触发。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。该失败为 BuildKit builder 实例被服务端主动回收导致的瞬时基础设施问题，与 PR 代码变更无关。直接 rerun 即可，无需修改任何代码。

## 需要进一步确认的点
- 无。本失败原因为基础设施建设问题（BuildKit builder 被服务端 graceful stop），日志证据充分，无需额外确认。

## 修复验证要求
不适用（infra-error，非代码修复）。
