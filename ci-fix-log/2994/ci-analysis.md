# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: failed to receive status, rpc error, closing transport, connection error, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`），约在执行 38.6 秒处
- 失败原因: BuildKit builder 实例（`euler_builder_20260709_224657`）在 Docker 构建过程中被外部终止（goaway 原因为 `graceful_stop`，错误码为 `NO_ERROR`），导致与 builder 的 RPC 连接断开，构建中断。这是 CI 基础设施问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。PR 仅新增了一个标准的 Dockerfile（安装 gcc、Python 3.9.19、pip 安装 scann==1.4.2）及配套元数据文件。失败发生在 `dnf install` 下载系统包阶段——这是一个纯粹的基础操作，未涉及任何 PR 特有的构建逻辑。BuildKit builder 被外部终止是基础设施层面的问题，即使回退 PR 变更也无法避免。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该失败为 BuildKit 基础设施临时故障（builder 被异常终止），与代码无关。建议在 CI 系统中重新触发该 job。如果连续多次重现相同错误，则需排查 CI 构建节点的资源限制（内存/磁盘/超时策略）或 BuildKit builder 的稳定性配置。

## 需要进一步确认的点
- 若重试后仍失败，需检查 CI 构建节点 `ecs-build-docker-x86-hk` 的资源状况（是否有 OOM killer 或磁盘空间不足导致 builder 被驱逐）
- 若仅 aarch64 构建节点也收到同类错误，则可能是 BuildKit builder 池的通用稳定性问题
