# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder意外终止
- 新模式症状关键词: no builder found, euler_builder, graceful_stop, closing transport, goaway, EOF, BuildKit, docker-container driver

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: BuildKit 构建基础设施层（`euler_builder_20260709_224657`），非代码文件行号
- 失败原因: Docker 镜像构建进行到第 2/4 步（`dnf install` 阶段，正在下载 openEuler 仓库元数据）时，BuildKit builder 实例（`euler_builder_20260709_224657`，使用 `docker-container` 驱动）被优雅关闭（`graceful_stop`），客户端连接中断（`EOF`），后续报 `no builder found`。dnf 仓库元数据下载速度仅 77 kB/s，耗时约 37 秒仅完成 2.8 MB，慢速下载可能触发了 CI 基础设施的超时或资源限制策略，导致 builder 被回收。

### 与 PR 变更的关联
与 PR 变更**无关**。本次 PR 仅新增了一个标准的 openEuler 24.03-LTS-SP4 Dockerfile 和对应的元数据文件，Dockerfile 内容（dnf 安装编译工具链 → 编译 Python 3.9.19 → pip 安装 scann）是标准镜像构建流程，与仓库中其他 scann Dockerfile（如 `24.03-lts-sp3`）结构一致。构建在 dnf 安装阶段即被基础设施中断，远未到达任何可能因 PR 改动引发问题的步骤。

## 修复方向

### 方向 1（置信度: 中）
**CI 基础设施问题，Code Fixer 无需处理。** 本次失败为 BuildKit builder 在构建过程中被意外终止，属于 CI runner 或 builder 基础设施层的问题（可能原因：资源配额、超时、builder 容器被 CI 平台回收等）。建议触发一次**重新运行 CI**（retry/re-run），若重试后通过，则确认本次为偶发性基础设施故障。

## 需要进一步确认的点
- CI 平台对该类型构建 job 的超时和资源限制配置（特别是 `docker-container` 驱动的 BuildKit builder 的最大存活时间）。
- dnf 仓库元数据下载速度仅 77 kB/s 是否因 CI runner 网络波动或 openEuler 镜像站限流导致（较异常，通常应在 MB/s 级别）。
- 是否有其他同时运行的 job 占用了 builder 资源，导致平台回收了该 builder 实例。
