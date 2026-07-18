# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器断开
- 新模式症状关键词: graceful_stop, no builder found, rpc error, closing transport, error reading from server: EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`，`dnf install` 下载软件仓库元数据阶段
- 失败原因: CI 使用的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行过程中被关闭（`graceful_stop`），导致构建会话中断。`dnf` 元数据下载耗时约 38.59 秒且速率极低（77 kB/s 下载 2.8 MB），可能触发了构建器空闲/运行超时，或被 CI 调度器主动回收。

### 与 PR 变更的关联
本次 PR 变更与 CI 失败**无直接关联**。PR 仅新增了 Dockerfile（安装基础构建依赖 `gcc gcc-c++ make wget` 等）、文档条目和 meta 配置。失败发生在 Docker 构建的第一个步骤（下载 dnf 仓库元数据），尚未触及任何 scann 或 Python 构建逻辑。这是纯粹的 CI 基础设施层面的问题——BuildKit 构建器在镜像拉取完成后的 `dnf install` 阶段失去连接。

## 修复方向

### 方向 1（置信度: 中）
本次失败属于 CI 基础设施问题（BuildKit 构建器连接断开），建议直接**触发 CI 重试**（re-run failed job）。若重试后仍然失败，则需要排查构建环境的网络状况（dnf 仓库元数据下载速率仅 77 kB/s 异常偏低）和 BuildKit builder 超时配置。

### 方向 2（置信度: 低）
若重试多次均在同一阶段失败，可能是 `euler_builder_*` 构建器的存活时间（TTL）配置过短，在 dnf 元数据下载期间超时被自动回收。此问题需由 CI 平台管理员调整构建器超时参数，与本次 PR 的 Dockerfile 内容无关。

## 需要进一步确认的点
1. 同 PR 的其他架构 job（如 aarch64）是否也失败？若 aarch64 job 成功，则进一步证实为 x86-64 runner 的临时基础设施问题。
2. CI 平台对 BuildKit builder 的 TTL / 超时配置是多少？当前 dnf 下载耗时 ~39 秒是否触及了阈值？
3. dnf 元数据下载速率（77 kB/s）异常偏低是否为该 runner 节点的普遍现象？可检查同 runner 上其他成功构建的 dnf 下载耗时对比。

## 修复验证要求
不适用。失败为 infra-error，无需修改 Dockerfile 或任何代码文件。Code Fixer 无需处理，建议重试 CI job。
