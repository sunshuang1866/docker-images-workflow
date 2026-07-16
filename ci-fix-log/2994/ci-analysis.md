# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder断连
- 新模式症状关键词: failed to receive status, rpc error, Unavailable, closing transport, no builder found

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`（dnf 正在下载仓库元数据时）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 dnf 安装依赖包阶段（步骤 2/4）意外断开连接。`graceful_stop` 调试数据表明该 builder 被主动终止（可能是 CI 节点资源不足或调度器回收 builder 容器），导致 RPC 连接丢失，后续步骤无法执行。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个标准的 Dockerfile（安装 gcc/openssl-devel/bzip2-devel/zlib-devel → 编译 Python 3.9.19 → pip 安装 scann 1.4.2），构建在第一个 `dnf install` 步骤（尚未执行到 Python 编译或 pip 安装阶段）即因 BuildKit builder 断连而失败。Dockerfile 本身的指令语法和包名均正确。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。这是 BuildKit 基础设施的瞬时故障（builder 实例被意外终止），与 PR 代码变更无关。重试后大概率可以通过。

## 需要进一步确认的点
- 如重试后仍失败，需检查 CI 构建节点（`ecs-build-docker-x86-hk`）的资源状况（内存/磁盘是否充足），以及 BuildKit builder 容器的 OOMKilled 或 eviction 事件日志
- 确认 `openeuler/openeuler:24.03-lts-sp4` 基础镜像仓库源在构建时是否稳定可访问（日志中 dnf 正在下载元数据时断连，不排除仓库源间歇性不可达触发超时导致 builder 被回收）

## 修复验证要求
无需验证（infra-error，与代码变更无关，重试 CI 即可）。
