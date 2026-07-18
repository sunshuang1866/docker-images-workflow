# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder连接中断
- 新模式症状关键词: graceful_stop, no builder found, closing transport, connection error, EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 第 2/4 步 (`RUN dnf install -y ...`)，无特定源码文件
- 失败原因: Docker BuildKit builder（`euler_builder_20260709_224657`）在执行 `dnf install` 下载仓库元数据过程中被基础设施层优雅终止（goaway `graceful_stop`），导致客户端连接断开、builder 实例随后被销毁，构建进程无法恢复

### 与 PR 变更的关联
**无关**。PR 变更仅为新增一个 Dockerfile 和更新 3 个元数据文件（README.md、doc/image-info.yml、meta.yml），不涉及任何可能影响 BuildKit 基础设施的行为。构建在执行 `dnf install` 下载阶段（尚未开始安装包）时 builder 被终止，属于 CI 基础设施层面的问题（如 runner OOM、节点资源回收、builder 超时自动清理等）。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发 CI 重试即可。** 这是典型的 CI 基础设施临时故障，BuildKit builder 实例在构建过程中被底层平台终止。重新触发 CI pipeline（retry）大概率可以成功通过。

## 需要进一步确认的点
- 如果重试后仍然失败，需要检查 CI runner 节点的资源情况（内存、磁盘、buildkit 容器日志），确认是否存在 OOM Kill 或节点自动缩容导致 builder 被清理
- 确认 `ecs-build-docker-x86-hk` runner 在 2026-07-09 22:46 左右的节点健康状况
