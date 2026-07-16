# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: graceful_stop, GOAWAY, no builder found, closing transport, rpc error

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` — 第一条 `RUN dnf install` 指令执行期间
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在 `dnf install` 下载元数据过程中（进度约 38%）被优雅终止（GOAWAY `graceful_stop`），导致 Docker 客户端与构建器之间的 gRPC 连接断开，构建中断

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 新增的 Dockerfile 内容语法正确，`dnf install` 安装的包（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）均为 openEuler 仓库中的常规构建依赖，不存在导致构建器崩溃的代码缺陷。错误发生在 BuildKit 基础设施层：构建器容器在构建过程中被外部因素（CI runner 资源不足、超时、或系统级清理策略）停止。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建。** 由于根因是 BuildKit 构建器被基础设施侧终止（graceful stop），与 Dockerfile 内容无关，最直接的验证方式是重跑 CI。如果多次重试均出现在相同步骤崩溃，则需排查 CI runner（`ecs-build-docker-x86-hk`）的资源状况（内存、磁盘空间、并发构建数上限）。

## 需要进一步确认的点
- CI runner `ecs-build-docker-x86-hk` 在构建时间点（2026-07-09 22:46 UTC+8）的内存和磁盘使用情况
- BuildKit 构建器 `euler_builder_20260709_224657` 的系统日志（OOM killer、容器驱逐记录等），确认是否为资源耗尽导致
- 同一时间段是否有其他构建任务争抢 runner 资源
- 如果多次重试均在同一 `dnf install` 步骤失败，需确认 `openeuler:24.03-lts-sp4` 基础镜像的 dnf repo 配置在该 runner 上是否可正常解析
