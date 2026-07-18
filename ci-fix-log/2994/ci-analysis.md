# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器被终止
- 新模式症状关键词: graceful_stop, no builder found, rpc error, closing transport, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `[7/8]`（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`）
- 失败原因: CI 的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 镜像构建过程中被终止（`graceful_stop`），导致与构建器的 RPC 连接断开，docker-container driver 无法继续执行构建。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个标准格式的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容为常规的 `dnf install` + Python 编译 + `pip install` 流程，语法正确。失败发生在 `dnf install` 下载仓库元数据阶段，此时尚未执行到任何 PR 特有的构建逻辑。BuildKit 构建器被终止属于 CI runner 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
本次失败为 **infra-error**，无需对 PR 代码做任何修改。建议直接 **re-trigger CI**，让构建在健康的 BuildKit builder 上重新运行。若多次重新触发后仍出现同样的 `graceful_stop` 错误，则需排查 CI runner 节点（`ecs-build-docker-x86-hk`）的资源状况或 BuildKit daemon 的稳定性。

## 需要进一步确认的点
- `euler_builder_20260709_224657` 构建器被终止的具体原因（内存不足 OOMKill？CI runner 超时？节点被抢占？）。这些信息通常不在应用层日志中记录，需要查阅 CI 平台（Jenkins）的节点/构建器管理日志。
- 若 retrigger 后持续失败，需确认同一时段是否有其他 PR 也遇到类似 Builder 消失的问题，以判断是否为集群级别故障。
