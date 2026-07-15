# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 断连
- 新模式症状关键词: closing transport, connection error, EOF, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`（dnf 元数据下载阶段）
- 失败原因: CI 创建的 BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被意外终止（debug data: `graceful_stop`），导致 BuildKit 客户端与 builder 的连接断开（`closing transport`），后续无法找到该 builder。Dockerfile 自身的 RUN 指令刚进入 dnf 元数据下载阶段（约 38 秒），尚未开始执行实际的包安装或编译操作。

### 与 PR 变更的关联
此失败与 PR 变更**无关**。PR 仅新增了一个标准 Dockerfile（安装编译依赖 → 编译 Python 3.9.19 → pip 安装 scann）及配套元数据文件。构建在第一个 `dnf install` 步骤的元数据下载阶段即因 BuildKit builder 断连而中断，Dockerfile 内容本身未被实际执行到。失败属于 CI 基础设施层面的 builder 进程异常终止。

## 修复方向

### 方向 1（置信度: 高）
此为 CI 基础设施故障（BuildKit builder 进程被终止），与 PR 代码变更无关。建议直接在 CI 系统中重新触发（re-run）该失败的 job。若重复出现，需检查 CI runner 节点的资源状况（内存、磁盘空间）及 BuildKit builder 的存活策略配置。

## 需要进一步确认的点
- CI runner 节点 `ecs-build-docker-x86-hk` 上 BuildKit builder 进程被 `graceful_stop` 的原因（可能是 OOM killer、磁盘空间不足、或 builder 超时策略触发）。
- 若重试后仍然失败，需排查该 runner 节点的系统日志（dmesg/journalctl）确认是否有 OOM 事件。
