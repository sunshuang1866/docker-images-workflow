# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, EOF, docker-container driver

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 第 7 步 (`dnf install`) 执行中（约 38 秒时）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 构建进行中被优雅关闭（`graceful_stop`，goaway code: `NO_ERROR`），导致与构建器的连接断开（`EOF`），构建中断。关闭后该构建器实例不再存在，无法恢复构建。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 仅新增了一个 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件（README.md、meta.yml、image-info.yml）。构建在第一个 `RUN` 步骤（`dnf install` 系统包）进行到约 38 秒时因 CI 基础设施问题中断——Dockerfile 本身的语法和逻辑尚未暴露出任何问题，因为构建甚至没有完成这个 `RUN` 步骤。

## 修复方向

### 方向 1（置信度: 高）
**无需修复 PR 代码。** 这是 CI 基础设施问题（BuildKit 构建器实例运行时被意外终止），属于 infra-error。应重新触发 CI 流水线（re-run）重试构建。如果持续复现，需排查 BuildKit builder（`docker-container` driver）的运行环境稳定性（如 runner 节点资源耗尽、OOM、构建器超时回收策略等）。

## 需要进一步确认的点
- BuildKit 构建器实例 `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因（是否因 CI 编排层的超时回收、节点资源压力触发驱逐，或运维操作导致）。
- 是否存在与 `euler_builder_` 构建器生命周期管理相关的 CI 配置问题（如 idle timeout 设置过短）。
