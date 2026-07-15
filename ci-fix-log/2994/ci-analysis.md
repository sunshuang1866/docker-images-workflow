# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 崩溃
- 新模式症状关键词: failed to receive status, Unavailable, closing transport, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install`（Dockerfile:11）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 Docker 镜像构建过程中意外终止/失联，`graceful_stop` goaway 信号表明 builder 容器被关闭，导致 `dnf install` 步骤进行到 38 秒时（正在下载软件包元数据）RPC 连接断开，构建中断。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了一个标准的 Dockerfile（安装 dnf 基础包、编译 Python 3.9.19、pip 安装 scann），以及 README、image-info.yml、meta.yml 的配套文档更新。Dockerfile 本身语法正确、依赖声明合理（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel` 均为标准构建依赖）。失败发生在 BuildKit 基础设施层，`dnf install` 步骤尚在正常执行（正在下载 metadata）时 builder 即被关闭，属于 CI Runner 侧的 BuildKit daemon 异常。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施故障（BuildKit builder 容器意外终止），与 PR 代码无关。只需**重新触发 CI 构建**即可。`graceful_stop` 表明 builder 可能被 Runner 节点上的资源调度器或超时策略回收，重试通常能解决。

## 需要进一步确认的点
- 确认 CI Runner 节点 `ecs-build-docker-x86-hk` 的健康状态和资源水位（内存/磁盘/CPU），排查 builder 被 OOM Killer 或磁盘满逐出的可能。
- 确认是否存在针对 BuildKit builder 的自动回收/超时策略导致正常构建被中断。
