# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器意外终止
- 新模式症状关键词: graceful_stop, no builder, rpc error, Unavailable, EOF, buildkit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install ...`（dnf 下载 OS 元数据阶段）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 `dnf install` 执行中被 CI 基础设施发送 `graceful_stop` 信号终止，导致 Docker 客户端与服务端的 RPC 连接断开（EOF），构建中断。构建器随后已不可用（"no builder found"），确认为 CI 侧主动回收/关闭了构建节点。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`（以及配套的 README、image-info.yml、meta.yml 更新），Dockerfile 内容为标准模式（安装 gcc/make 等基础编译工具 → 编译 Python 3.9 → pip 安装 scann），与已有 sp3 版本结构一致，不存在能导致 BuildKit 构建器崩溃的代码。构建在 `dnf install` 下载阶段即因基础设施问题中断，未进入任何 PR 引入的定制逻辑。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试。** 这是 CI 基础设施问题（BuildKit 构建器被管理面回收），与代码变更无关。重新触发 CI 流水线（re-trigger / re-run）大概率可通过。如果多次重试均在相同阶段失败，则需排查 CI 构建节点资源（内存、磁盘）是否不足导致 `dnf` 下载元数据时触发 OOM 被 kill。

## 需要进一步确认的点
- CI 构建节点 `ecs-build-docker-x86-hk` 在构建时段是否有资源压力或维护操作导致 BuildKit 实例被回收
- 重新触发后是否仍然在同一 `dnf install` 阶段失败（如果是，则可能存在节点镜像缓存损坏等问题，而非纯 infra 偶发故障）
