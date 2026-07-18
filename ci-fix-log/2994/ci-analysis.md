# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 连接中断
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, Unavailable, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7（Dockerfile 指令 2/4，即 `dnf install` 步骤）
- 失败原因: CI 构建所用的 BuildKit builder 实例（`euler_builder_20260709_224657`）在 `dnf install` 下载系统包过程中被外部终止（gRPC `graceful_stop` goaway 帧），导致 BuildKit 客户端与 builder 之间的连接断开，构建中断。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个标准的 ScaNN Dockerfile（安装编译依赖 → 编译 Python 3.9.19 → pip 安装 scann），以及配套的 README、image-info.yml、meta.yml 元数据更新。`dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel` 是合法且常见的依赖安装命令。失败发生在 `dnf` 下载系统元数据（耗时约 38 秒后）时，BuildKit builder 被 CI 基础设施意外终止，属于纯粹的基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 该失败为 CI 基础设施问题（BuildKit builder 实例在构建中途被外部终止），与 PR 的 Dockerfile 或元数据变更无关。建议：
- 重新触发 CI 构建（retry），大概率可通过。
- 若反复出现，需排查 Jenkins executor 节点的资源情况（内存是否不足导致 OOM Kill）或构建超时配置。

## 需要进一步确认的点
- Jenkins executor `ecs-build-docker-x86-hk` 在构建期间是否存在资源耗尽（内存/磁盘）或超时触发。
- `euler_builder_20260709_224657` BuildKit 实例是否被外部清理脚本或容器生命周期管理策略提前回收。
- 若重试后仍失败，需提供重试日志以排除间歇性网络问题。

## 修复验证要求
无需验证（infra-error，非代码问题）。
