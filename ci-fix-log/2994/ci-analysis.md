# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器终止
- 新模式症状关键词: graceful_stop, closing transport, error reading from server: EOF, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile 第一个 `RUN dnf install` 步骤（Dockerfile 第 6-9 行）
- 失败原因: BuildKit builder 容器（`euler_builder_20260709_224657`）在执行 `dnf install` 的元数据下载阶段被异常终止（GOAWAY `graceful_stop`），导致 Docker 客户端与服务端之间的 transport 连接断开（`error reading from server: EOF`），构建中断。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 此次 PR 仅新增了一个标准格式的 Dockerfile（安装构建依赖 → 编译 Python 3.9.19 → pip 安装 scann）和配套的元数据文件。构建中断发生在 `dnf install` 下载 openEuler 24.03-lts-sp4 仓库元数据过程中，属于 CI 构建基础设施层的故障（builder 容器被服务端主动关闭），Dockerfile 本身的指令无任何语法或逻辑问题。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 流水线。** 此失败为 BuildKit 基础设施瞬时故障，与 PR 代码无关。建议手动重新触发 workflow（Re-run），大多数情况下 builder 资源恢复正常后构建可顺利完成。若多次重试仍复现，需排查 CI runner 节点（`ecs-build-docker-x86-hk`）上的 BuildKit daemon 资源状况（内存、磁盘、builder 实例数上限等）。

## 需要进一步确认的点
1. 同一时间段内是否有其他 PR 的 CI 构建也因类似 `graceful_stop` / `no builder found` 错误而失败——若存在，可确认为 CI 基础设施的批量性问题。
2. `ecs-build-docker-x86-hk` runner 节点的 BuildKit daemon 日志，确认 `graceful_stop` 的触发原因（是资源限制、运维重启、还是 daemon 崩溃）。
3. 重跑 CI 后观察是否通过，若仍然失败则需进一步排查 builder 节点健康状态。
