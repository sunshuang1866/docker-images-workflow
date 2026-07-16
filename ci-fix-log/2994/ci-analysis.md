# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 构建器异常停止
- 新模式症状关键词: graceful_stop, no builder found, rpc error, Unavailable, closing transport, error reading from server: EOF

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: BuildKit 构建器 `euler_builder_20260709_224657`（Docker 构建守护进程）
- 失败原因: Docker 构建进行到第 7 步（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）时，BuildKit 构建器实例 `euler_builder_20260709_224657` 收到 `graceful_stop` 信号后主动关闭了连接，导致 RPC 传输中断、构建失败。`graceful_stop` 为 GOAWAY 帧中携带的调试信息，表示服务端主动发起了优雅关停，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。该 PR 仅做了以下纯新增/文档修改：
1. 新增 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`（21 行新文件）
2. 更新 `Others/scann/README.md`（添加新版本表格行）
3. 更新 `Others/scann/doc/image-info.yml`（添加新版本条目）
4. 更新 `Others/scann/meta.yml`（添加新版本路径映射）

Dockerfile 内容正确无语法错误，构建在前 6 步均正常完成（加载基础镜像、拉取层），在第 7 步执行 `dnf install` 中途被 BuildKit 构建器异常关停。失败原因是 CI 基础设施层面的问题（构建器被关闭），不是 Dockerfile 代码问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。失败原因是 CI 基础设施中 BuildKit 构建器实例在构建中途被优雅关停（可能由于宿主机资源调度、构建器池回收、超时策略等），属于临时性基础设施故障。重新触发 CI pipeline，构建器大概率正常工作。

### 方向 2（置信度: 低）
若重试后仍反复出现相同错误，需检查 CI 构建平台中 `euler_builder_*` 实例的生命周期策略（是否设置了过短的 TTL），或检查 `ecs-build-docker-x86-hk` 节点的资源状态。

## 需要进一步确认的点
1. 构建器 `euler_builder_20260709_224657` 被 graceful_stop 的具体原因（CPU/内存超限、节点调度驱逐、构建器池超时回收等），需查阅 CI 编排平台的构建器管理日志。
2. 是否同时间段其他 PR 的 x86-64 构建也出现相同错误，以判断是单点故障还是平台级问题。
