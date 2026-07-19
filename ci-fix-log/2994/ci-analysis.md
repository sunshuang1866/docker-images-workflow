# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: closing transport, EOF, graceful_stop, no builder found

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`）
- 失败原因: CI 的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建过程中被强制终止（goaway frame 携带 `graceful_stop` 调试信息），导致与 builder 的 gRPC 连接断开，后续步骤无法找到该 builder。

### 与 PR 变更的关联
该失败与 PR 变更 **无关**。PR 新增的 Dockerfile 内容本身没有语法或逻辑错误——`dnf install` 列出的包均为 openEuler 标准仓库中的常规编译依赖，且在故障发生时 `dnf` 正在正常下载元数据阶段。错误本质是 CI 基础设施中的 BuildKit 构建器被外部因素（如节点资源回收、调度器重分配等）强制关闭。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。该失败为 CI 基础设施问题（BuildKit builder 在构建中途被终止），建议直接 **rerun CI job**。若多次 rerun 仍出现在同一位置失败，需排查 CI 构建节点的稳定性（如内存不足导致 OOM、磁盘空间不足、或节点调度策略异常）。

## 需要进一步确认的点
- CI 构建节点 `ecs-build-docker-x86-hk` 在构建时段是否存在资源压力或节点维护事件。
- 同一时段是否有其他 PR 的构建也遭遇相同的 builder 终止问题，以判断是个例还是集群级故障。

## 修复验证要求
无代码修复，因此无需额外验证步骤。建议 rerun CI 后确认构建通过即可。
