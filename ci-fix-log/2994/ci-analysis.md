# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 宕机
- 新模式症状关键词: rpc error, closing transport, connection error, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`（启动约 38 秒后被中断）
- 失败原因: BuildKit 构建节点 `euler_builder_20260709_224657` 在执行 `dnf install` 下载 OS 元数据期间宕机/断开连接，gRPC transport 报 "closing transport" + "graceful_stop"，构建连接中断后 builder 实例销毁消失。

### 与 PR 变更的关联
**与 PR 无关**。构建在 docker build 的第一步包安装（`dnf install` 基础编译工具链）阶段就因基础设施故障中断，尚未触及任何与 PR 代码变更相关的步骤（Python 编译、scann pip 安装等）。Dockerfile 语法正确，`FROM` 镜像拉取成功，包安装命令本身无错误——故障仅发生在 BuildKit builder 节点的网络连接层面。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 这是 CI 基础设施问题——BuildKit builder 节点在构建中途崩溃或网络中断。应重试该 job 或由 CI 运维检查 `euler_builder_20260709_224657` 对应节点的健康状况（是否因内存不足 OOM、Docker daemon 重启、网络波动等导致 gRPC 连接断开）。

## 需要进一步确认的点
（无——日志证据充分，属于明确的 infra-error）

## 修复验证要求
（不适用——infra-error，无代码修复）
