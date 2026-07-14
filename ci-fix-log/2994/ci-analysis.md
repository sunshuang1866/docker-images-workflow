# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器断开
- 新模式症状关键词: closing transport, connection error, graceful_stop, no builder found

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 构建上下文
- 构建已成功完成前置步骤：基础镜像拉取（`FROM docker.io/openeuler/openeuler:24.03-lts-sp4`）正常完成（步骤 `[1/4]`）。
- 失败发生在步骤 `[2/4]`：`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`
- DNF 正在下载元数据时（`OS 77 kB/s | 2.8 MB 00:37`），BuildKit 构建器实例 `euler_builder_20260709_224657` 突然断开连接。

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`RUN dnf install ...`）
- 失败原因: BuildKit 构建器实例被外部因素关闭（goaway 标记为 `graceful_stop`），导致 Docker 构建进程与构建器之间的 gRPC 连接断开，传输层报 EOF 错误。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个标准 Dockerfile（引入 scann 1.4.2 镜像），其 `dnf install` 命令格式与仓库中其他同类 Dockerfile 一致。Dockerfile 语法正确、依赖声明完整（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`），构建未进入编译或 pip install 阶段即已失败。失败原因为 CI 基础设施层面的 BuildKit 构建器异常终止，属于偶发性基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 此为 CI 基础设施故障（BuildKit 构建器实例被意外回收/关闭），与代码或 Dockerfile 内容无关。无需任何代码修改，直接重新触发 CI 流水线即可。若反复重试仍失败，考虑以下方向：

### 方向 2（置信度: 低）
若多次重试均在同一位置（`dnf install` 下载阶段）失败，可能是构建节点的 Docker BuildKit 构建器资源池不稳定，需联系 CI 基础设施运维团队排查调度器/构建器回收策略。

## 需要进一步确认的点
- 该构建器实例 `euler_builder_20260709_224657` 是否因超时策略被回收（日志中未显示明显超时信息）。
- 同一时间段的 CI 节点 `ecs-build-docker-x86-hk` 上其他构建任务是否也遇到相同问题，以确认是否为节点级别故障。
- `aarch64` 架构构建任务是否也失败（PR diff 中 `meta.yml` 未限定 `arch`，CI 应同时在 x86_64 和 aarch64 上构建；日志仅包含 x86_64 runner 输出）。
