# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: graceful_stop, no builder, closing transport, connection error, EOF, rpc error

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: BuildKit 构建步骤 `#7 [2/4] RUN dnf install ...`，dnf 正在下载仓库元数据时
- 失败原因: CI 基础设施的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行过程中被服务端主动关闭（`graceful_stop` goaway 帧），导致 gRPC 连接中断、构建器实例消失，docker build 进程无法继续

### 与 PR 变更的关联
**与 PR 改动无关**。PR 新增的 Dockerfile 内容（安装编译依赖、编译 Python、pip 安装 scann）是标准操作，失败发生在 dnf 下载仓库元数据的第 38.59 秒，此时尚未进入任何与 PR 特有逻辑相关的步骤（Python 编译在步骤 [3/4]、scann 安装在步骤 [4/4]）。构建器实例被 CI 平台侧回收/重启导致了此次失败，属基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，代码无需修改。应重新触发 CI 构建（retry），如果同一个节点 `ecs-build-docker-x86-hk` 反复出现此类问题，需由 CI 运维排查该节点的 BuildKit builder 是否因资源不足（内存/磁盘）或配置问题被频繁回收。

## 需要进一步确认的点
- 同一时间段其他 PR 是否也在该节点 (`ecs-build-docker-x86-hk`) 上出现类似的 `graceful_stop` / `no builder found` 错误，以确认是否为节点级故障
- CI 平台是否有构建超时策略导致 long-running build 被主动终止（dnf 下载 2.8 MB 元数据耗时 38.59 秒可能较慢，但不致触发超时）
