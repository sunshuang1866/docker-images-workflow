# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器断开
- 新模式症状关键词: graceful_stop, no builder found, euler_builder, closing transport, EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile 第 7 行附近（`dnf install` 步骤，对应新 Dockerfile 中的 `RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）
- 失败原因: Docker BuildKit 构建器实例 `euler_builder_20260709_224657` 在 `dnf install` 下载元数据阶段被主动关闭（`graceful_stop`），客户端与服务端的 gRPC 连接断开，构建中断。`dnf` 下载 OS 仓库元数据时速率仅 77 kB/s（预计还需 37 秒），慢速下载可能触发了 CI 构建器超时回收机制。

### 与 PR 变更的关联
与 PR 代码变更无直接因果关联。PR 新增的 Dockerfile 本身语法正确，`dnf install` 所列包名均为 openEuler 仓库中的标准包，构建流程正常推进至 `dnf install` 步骤后才因 CI 基础设施层面（构建器断开）而失败。该失败属于 CI 基础​​设施问题，非代码缺陷。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。该错误为 CI 构建器在慢速网络下载中因超时/回收被终止，属于偶发性基础设施问题。Code Fixer 无需修改任何代码或 Dockerfile，重新触发 CI 流水线（retry）有较大概率通过。

### 方向 2（置信度: 低）
若多次重试均在同一阶段失败，可能是 `dnf install` 所需元数据下载过慢（77 kB/s）持续触发构建器超时保护。可考虑更换 `dnf` 仓库镜像源（如将默认 repo 替换为更快的内网镜像），或增加 CI 构建器超时阈值。但这对当前 PR 的 Dockerfile 而言并非必要修改。

## 需要进一步确认的点
- 该构建器实例 `euler_builder_20260709_224657` 是否有明确的超时时间限制（如 60 秒或 120 秒），以及 `dnf` 慢速下载是否刚好触及该阈值。
- 该错误是否在同批次的其他 PR 构建中也出现（判断是否为 CI 集群级别的临时故障）。
- `dnf` 从 OS 仓库拉取元数据 2.8 MB 耗时 37+ 秒（77 kB/s）是否仅为临时网络抖动。

## 修复验证要求
若选择方向 1（重试），验证方式为重新触发 CI 流水线，确认构建完整通过即可。
若后续重试仍然失败且确认并非 CI 基础设施问题，则需获取更完整的构建日志（包含 dnf install 的完整输出和被中断前的最后日志行），重新定位根因。
