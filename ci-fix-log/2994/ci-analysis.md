# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器丢失
- 新模式症状关键词: closing transport, graceful_stop, no builder found, euler_builder, rpc error, Unavailable, EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile 第 2/4 步 `RUN dnf install -y ...`（构建阶段，非 PR 代码行）
- 失败原因: Docker 构建过程中，BuildKit 构建器实例 `euler_builder_20260709_224657` 被优雅关闭（`graceful_stop`），导致连接丢失，`dnf install` 步骤在下载系统元数据时被中断。此错误属于 CI 基础设施问题（构建器节点不稳定或资源调度异常），与 PR 的 Dockerfile 变更无关。

### 与 PR 变更的关联
无关。PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 以及更新其对应的 README.md、image-info.yml、meta.yml，Dockerfile 语法正确、依赖声明完整（遵循与已成功的 24.03-lts-sp3 相同模式）。构建尚未到达与代码逻辑相关的阶段即因构建器崩溃而失败。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。此次失败是 BuildKit 构建器实例在构建过程中意外消失导致的瞬时性基础设施故障，PR 代码无实质问题。重试 CI 大概率可以通过。

## 需要进一步确认的点
- CI 构建节点 `ecs-build-docker-x86-hk` 在该时间段的资源负载或调度日志，确认是否为节点异常重启/回收导致构建器实例被销毁。
- 如果重试后仍反复失败，需检查 BuildKit 构建器池的容量与稳定性配置。

## 修复验证要求
无需代码修复。重新触发 CI 构建即可验证。
