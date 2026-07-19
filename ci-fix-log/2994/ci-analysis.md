# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 丢失
- 新模式症状关键词: no builder found, error reading from server: EOF, graceful_stop, failed to receive status

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[7/7] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`（执行中）
- 失败原因: CI 构建环境的 BuildKit builder 实例 `euler_builder_20260709_224657` 在 Docker 构建进行中被异常终止（goaway 原因为 `graceful_stop`），导致 BuildKit 客户端失去与 builder 的连接。构建正在执行 `dnf install` 的元数据下载阶段（`OS 77 kB/s | 2.8 MB 00:37`）时 builder 丢失。这是 CI 基础设施层面的故障，与 PR 代码变更无关。

### 与 PR 变更的关联
无关。PR 仅新增了一个标准的 Dockerfile（安装基础编译工具链 + Python 3.9 + pip 安装 scann），Docker 构建正常启动（base image 拉取成功、Dockerfile 解析成功），但在 `dnf install` 执行到约 37 秒时 builder 容器被 CI 基础设施终止。Dockerfile 本身无语法错误、无依赖缺失、无版本冲突。

## 修复方向

### 方向 1（置信度: 高）
此为 CI 基础设施故障（BuildKit builder 实例异常丢失），**Code Fixer 无需处理**。应由 CI 运维团队排查以下可能原因：
- CI runner（`ecs-build-docker-x86-hk`）上的 BuildKit builder 容器是否因资源水位（内存/磁盘）被 OOM Killer 或调度器终止
- `euler_builder_20260709_224657` builder 实例的生命周期管理是否存在 bug（如提前回收）
- `dnf` 元数据下载阶段网络延迟（77 kB/s 下载 2.8 MB）是否触发了 CI job 的隐形超时

建议在 CI 侧重新触发此 job。若重试后仍失败，再考虑是否为 `openeuler:24.03-lts-sp4` 基础镜像的 dnf repo 配置导致下载极度缓慢、进而引发 builder 超时。

## 需要进一步确认的点
- `euler_builder` 实例的日志或生命周期事件（需要 CI 运维团队查看 builder 容器/进程的终止原因）
- CI job 的整体超时配置与 `dnf install` 实际耗时之间的关系
- 同一 CI runner 上同期是否有其他 job 争抢资源导致 builder 被驱逐

## 修复验证要求
（无需验证，此为 infra-error，Code Fixer 不需要提交任何代码修改。建议 CI 运维侧重试构建。）
