# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 意外终止
- 新模式症状关键词: graceful_stop, no builder found, connection error, EOF, rpc error, reading from server

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: 不适用（非代码层面错误）
- 失败原因: Docker BuildKit builder 容器（`euler_builder_20260709_224657`）在 `dnf install` 下载元数据过程中被优雅终止（graceful_stop），导致 BuildKit gRPC 连接断开，构建任务中断。这是 CI 基础设施层面的问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及其配套的 README、image-info.yml、meta.yml 条目。Dockerfile 中的 `dnf install` 命令语法正确，所列包名（gcc、gcc-c++、make、wget、openssl-devel、bzip2-devel、zlib-devel）均为 openEuler 有效包名。构建在 dnf 元数据下载阶段因 BuildKit builder 消失而中断，而非因 dnf 命令本身或包依赖错误失败。该失败与此次 PR 的代码变更**无因果关系**。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该失败是 CI 基础设施的 BuildKit builder 容器被意外回收/终止所致（`graceful_stop` + `no builder found`），属于瞬时基础设施故障。重新触发 CI job 即可验证 Dockerfile 是否能正常构建通过。

## 需要进一步确认的点
- 确认 CI 平台的 BuildKit builder 回收策略（是否存在空闲超时或资源配额限制导致 builder 被终止）
- 此次构建仅涉及 x86-64 架构（日志 runner 为 `ecs-build-docker-x86-hk`），如果该镜像同样需要在 aarch64 上构建，需确认 aarch64 job 是否也存在类似基础设施问题
