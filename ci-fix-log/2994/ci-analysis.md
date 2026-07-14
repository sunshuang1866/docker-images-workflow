# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 异常终止
- 新模式症状关键词: graceful_stop, rpc error, Unavailable, no builder found, euler_builder

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel` 执行期间
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在执行 dnf 元数据下载过程中被服务端主动发送 `graceful_stop` goaway 帧终止，随后 RPC 连接中断（EOF），构建器实例销毁，导致后续重试时无法找到该 builder。

### 与 PR 变更的关联
PR 变更内容为新增 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套元数据文件，Dockerfile 语法和内容均符合现有同类镜像的规范模式，未见明显错误。失败发生在 Dockerfile 中常规的 `dnf install -y` 包安装步骤，并非由 PR 代码变更的逻辑缺陷触发。失败更可能是 CI 基础设施侧（BuildKit builder 进程）的临时性问题引起。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题，非代码问题。建议：
1. **重新触发 CI 构建**：该 Dockerfile 无逻辑错误，重试构建大概率可成功。
2. **排查 BuildKit builder 终止原因**：检查 CI 节点（`ecs-build-docker-x86-hk`）是否因资源不足（内存/OOM、磁盘空间）或超时策略导致 builder 被 kill。日志中 dnf 元数据下载速度为 77 kB/s，2.8MB 元数据需约 37 秒完成；若 CI 对 builder 有生存时间限制或节点负载过高，可能导致 builder 在这段时间内被清理。
3. **检查 dnf 仓库连通性**：确认 CI 节点到 openEuler 24.03-LTS-SP4 软件源（`OS` repo）的网络延迟和带宽是否正常，77 kB/s 的下载速度偏低。

## 需要进一步确认的点
- `graceful_stop` 是 BuildKit daemon 主动发出的关闭信号，需要确认触发原因：是 CI Job 超时策略、Jenkins 节点清理机制，还是 Builder 进程自身的内存/crash 问题。
- 检查同一时间段内其他类似 PR（同为 24.03-lts-sp4 基础镜像的构建）是否也出现相同错误，以区分是节点级问题还是该基础镜像的 dnf 仓库问题。
- 若重试后仍失败，需获取 BuildKit builder 容器的日志（`docker logs buildx_buildkit_euler_builder_20260709_2246570`）以确定 builder 侧崩溃的精确原因。
