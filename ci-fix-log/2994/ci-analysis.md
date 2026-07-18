# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, connection error, EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`dnf install` 阶段）
- 失败原因: CI 的 BuildKit builder 实例（`euler_builder_20260709_224657`）在执行 `dnf` 包安装过程中被 `graceful_stop` 信号终止，导致客户端与 builder 之间的 gRPC 传输连接断开（`connection error: EOF`），构建进程被迫中断。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile（安装 dnf 包 → 编译 Python 3.9.19 → pip install scann）及相关元数据文件。构建在依赖安装阶段（`[2/4]`）因 CI 基础设施中断而失败，尚未执行到任何与 PR 具体内容相关的步骤（如 Python 编译或 scann 安装）。Dockerfile 语法和依赖声明均无问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是一个 CI 基础设施故障：BuildKit builder 被 `graceful_stop` 提前终止。Code Fixer 无需对 Dockerfile 或元数据文件做任何修改。应直接在 CI 平台重新触发该 workflow / job，让构建在可用的 builder 实例上重新运行。

## 需要进一步确认的点
- 确认 `graceful_stop` 是否由 CI 系统超时策略、节点资源回收、或运维操作（如节点下线）触发。若反复出现同类报错，需要联系 CI 基础设施团队排查 builder 节点的稳定性。
- 确认重试后构建是否能正常通过——如果重试依然在同一步骤失败，则需进一步获取 builder 端日志（而非仅客户端日志）来排除 `dnf` 下载源连通性问题。

## 修复验证要求
无。此失败为 infra-error，修复方向为重试而非代码变更，无需验证步骤。
