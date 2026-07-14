# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 丢失
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, Unavailable, docker-container driver

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建层 #7（`dnf install` 步骤），BuildKit `euler_builder_20260709_224657` 实例
- 失败原因: 构建过程中 BuildKit builder 实例（docker-container driver）被服务端主动关闭（GOAWAY 帧，`graceful_stop`），导致客户端无法继续通信，构建中断。此错误与 PR 代码变更完全无关，属于 CI 基础设施层的 builder 生命周期问题。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增 4 个文件（Dockerfile、README.md 更新、image-info.yml 更新、meta.yml 更新），均为标准的文档/配置变更。新增 Dockerfile 中 `dnf install` 步骤的包名和语法均正确，不存在导致构建环境崩溃的可能。失败发生在 dnf 下载元数据阶段（尚未开始安装任何软件包或编译 Python），是 BuildKit 容器被外部因素终止。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施的临时性问题：BuildKit builder 容器（`euler_builder_20260709_224657`）在执行过程中被服务端主动发送 GOAWAY 终止。常见原因包括：
- BuildKit daemon 端因资源压力（内存/磁盘不足）或超时策略自动回收 builder
- CI 节点的 Docker daemon 重启或维护操作
- 网络抖动导致 gRPC 长连接断开

**建议操作**: 重新触发 CI 运行（re-run the failed job）。若重试后仍失败，需排查 CI 节点的 BuildKit daemon 日志和资源使用情况。

## 需要进一步确认的点
- 若多次重试均在同一位置（`dnf install` 阶段）失败，需排查 CI 节点是否对 `openeuler/openeuler:24.03-lts-sp4` 基础镜像的拉取或 dnf 仓库访问有限制
- 若重试成功，则确认本次为偶发性基础设施故障，PR 代码无需任何修改

## 修复验证要求
无。此故障为 infra-error，不涉及任何代码修改。
