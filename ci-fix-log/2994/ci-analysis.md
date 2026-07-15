# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器连接丢失
- 新模式症状关键词: failed to receive status, rpc error, Unavailable, closing transport, EOF, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建 Step #7 [2/4]（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`）
- 失败原因: Docker BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 下载系统包时被服务端主动关闭（`graceful_stop`），导致 gRPC 传输连接中断，客户端收到 EOF 后无法继续构建。该错误与 PR 代码变更无关，属于 CI 基础设施问题。

### 与 PR 变更的关联
PR 变更内容为新增 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及相关元数据文件（README.md、doc/image-info.yml、meta.yml）。Dockerfile 本身无语法错误，构建在基础镜像拉取成功后、包安装阶段因 builder 崩溃而中断。日志中无任何由 PR 代码引起的编译错误、依赖缺失或测试失败，**失败与 PR 改动无直接因果关系**。

## 修复方向

### 方向 1（置信度: 中）
**重试 CI 构建**。该失败为 BuildKit builder 实例被异常终止导致的瞬时性基础设施故障。日志显示 dnf 包下载速度极慢（77 kB/s，2.8 MB 耗时 37 秒），可能导致构建耗时过长触发 builder 超时清理或资源回收。无需修改任何代码，触发 CI 重新构建即可。

### 方向 2（置信度: 低）
**检查 CI 节点资源与超时配置**。如果重试后仍然在同一位置失败，可能是 CI 节点的磁盘空间、内存不足或 builder 超时阈值过低导致长耗时构建被强制终止。需要联系 CI 运维排查 `ecs-build-docker-x86-hk` 节点的资源状况。

## 需要进一步确认的点
- 需确认 aarch64 架构构建 job 的日志状态（当前仅提供了 x86-64 job 日志），以排除架构专属问题。
- 如重试后仍失败，需确认 CI builder 的超时阈值设置以及构建节点的可用资源（磁盘、内存）。
- 日志中 dnf 下载速度仅 77 kB/s，需确认 CI 节点到 openEuler 软件源之间的网络是否存在异常。

## 修复验证要求
不适用（infra-error，无需修改代码）。
