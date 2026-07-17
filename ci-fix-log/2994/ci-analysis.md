# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器超时中断
- 新模式症状关键词: graceful_stop, no builder found, closing transport, EOF, buildx, docker-container driver

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段，步骤 `[2/4]`（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 dnf 安装过程中被优雅关闭（`graceful_stop`），gRPC 连接中断导致构建失败。dnf 下载元数据速度仅 77 kB/s（耗时 38.59 秒仅完成 OS repo），慢速下载可能触发了 CI 构建超时或 runner 资源限制。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`），其内容为标准模式：`dnf install` 安装编译工具链 → 编译 Python 3.9.19 → `pip install scann`。Dockerfile 语法正确、包名合理（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel` 均为 openEuler 仓库已有包）。构建在中途被基础设施中断，dnf 命令本身未报任何错误。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题，**Code Fixer 无需修改任何代码**。建议重试 CI 构建。若反复出现同样错误，需排查 CI runner 的网络带宽、构建超时设置（buildx builder 的 `--driver-opt` 超时参数），或考虑为 dnf 命令添加 `--retries` 重试机制。

## 需要进一步确认的点
1. 该 PR 是否仅发生在 x86-64 架构构建中（日志显示 runner 为 `ecs-build-docker-x86-hk`），aarch64 构建是否成功。
2. CI 构建的超时配置（`BuildKit` 的 `BUILDKIT_SESSION_TIMEOUT` 或 buildx `--driver-opt network=host` 等参数），确认 38+ 秒的 dnf 元数据下载是否会触发构建器超时回收。
3. 该 runner 的网络状况：dnf 下载速度仅 77 kB/s，需确认是否为临时性网络拥塞。
