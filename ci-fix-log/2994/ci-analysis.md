# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被停止
- 新模式症状关键词: rpc error, Unavailable, closing transport, graceful_stop, no builder found

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 `dnf install` 下载元数据过程中（耗时约 38 秒，速率仅 77 kB/s）主动发送了 `graceful_stop` 的 goaway 帧后断开连接，导致 Docker 构建过程中断。这是 CI 基础设施层面的问题（构建器被回收/超时终止），与 PR 代码变更无关。

### 与 PR 变更的关联
无关联。PR 仅新增一个合法的 Dockerfile（安装 scann 1.4.2 于 openEuler 24.03-lts-sp4）及相关元数据/文档文件。Dockerfile 语法正确，`dnf install` 的包列表（gcc, gcc-c++, make, wget, openssl-devel, bzip2-devel, zlib-devel）均为 openEuler 仓库中的标准包，不存在拼写错误或不存在的包名。构建失败纯粹因为 BuildKit 基础设施在 `dnf` 下载阶段意外终止。

构建过程的前置步骤（#1 启动 BuildKit、#2 加载 Dockerfile、#3 拉取基础镜像元数据、#5 加载 .dockerignore、#6 拉取并解压基础镜像）均正常完成，进一步佐证 Dockerfile 本身没有问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。本次失败是 CI 基础设施的偶发问题（BuildKit 构建器在 `dnf install` 过程中被回收/终止），与 PR 代码无关。重新触发 CI 流水线即可。如果重试后仍然失败，则需检查 CI runner 的资源配额（内存、磁盘）或超时设置。

## 需要进一步确认的点
- CI runner `ecs-build-docker-x86-hk` 的资源使用情况（内存、磁盘空间是否充足）
- BuildKit 构建器 `euler_builder_20260709_224657` 是否因超时策略被回收
- `dnf` 下载速率极低（77 kB/s）是否触发了网络超时
