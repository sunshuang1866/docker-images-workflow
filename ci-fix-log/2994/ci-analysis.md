# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit优雅终止
- 新模式症状关键词: graceful_stop, buildkit, euler_builder, connection error, EOF, error reading from server

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`，即新增 Dockerfile 中的 `RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all` 阶段
- 失败原因: Docker BuildKit builder 实例（`euler_builder_20260709_224657`）在 `dnf install` 下载包元数据过程中被优雅终止（`graceful_stop`），导致构建连接断开。下载速度仅 77 kB/s，耗时 37 秒下载 2.8 MB 元数据，可能因构建步骤超时或 CI runner 资源回收触发 builder 终止。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 新增的 Dockerfile 语法和包列表正确，`dnf install` 命令本身没有问题。失败是 CI 基础设施层面 BuildKit 服务被终止所致，属于 `infra-error`。该 Dockerfile 在下次 CI 触发时，若基础设施正常，极大概率可成功构建。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 即可。** 本次失败为 BuildKit builder 实例被 infra 层优雅终止导致的临时性故障，与 PR 新增的 Dockerfile 内容无关。推荐操作：在 PR 页面 comment `/retest` 或等同操作重新触发 CI。

## 需要进一步确认的点

1. 若重试后仍失败，需检查 CI runner（`ecs-build-docker-x86-hk`）的网络状况和 BuildKit builder 的超时配置阈值是否过短（当前仅 37 秒下载 2.8 MB 即触发终止，下载速度异常偏低）。
2. 若重试后仍失败，需确认 `openeuler/openeuler:24.03-lts-sp4` 基础镜像内置的 dnf repo 配置在中国香港 runner 上的可用性和下载速度是否正常。
