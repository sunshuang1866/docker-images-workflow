# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器断开
- 新模式症状关键词: graceful_stop, no builder, closing transport, EOF, rpc error, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建器 `euler_builder_20260709_224657`（非 PR 代码中任何文件）
- 失败原因: CI 构建节点上的 BuildKit 守护进程向构建器实例发送了 `graceful_stop`（GOAWAY frame，code: NO_ERROR），随后连接断开。构建器在 Dockerfile 第 2/4 步（`dnf install` 下载 OS 元数据阶段，已执行约 39 秒）时被终止，导致后续步骤无法继续。

### 与 PR 变更的关联
**无关。** 此次 PR 变更仅新增了 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容为标准的 `dnf install` 基础依赖 + Python 3.9.19 源码编译 + `pip install scann`。构建失败发生在 `dnf install` 下载仓库元数据的中途，根因是 BuildKit 构建器实例被 CI 基础设施回收/终止，与 PR 代码逻辑无关。

## 修复方向

### 方向 1（置信度: 高）
**无需 PR 代码修改。** 该失败属于 CI 基础设施问题（BuildKit builder 被意外终止），应通过重新触发 CI job 重试。如果反复出现同类错误，需检查 CI 构建节点的资源配额（内存/磁盘/超时设置）或 BuildKit daemon 的稳定性。

## 需要进一步确认的点
- CI 构建节点 `ecs-build-docker-x86-hk` 在构建时间段（2026-07-09 22:46 左右）是否存在资源紧张、节点维护或被抢占的情况。
- BuildKit builder 实例的 TTL/超时配置是否足够完成 `dnf install` 步骤（当前该步骤执行约 39 秒后被终止）。
- 如果 JOB 状态确认为 CI_Failure 且反复重试仍失败，则可能不是单纯的 infra-error，需要获取更完整的 Runner 日志进一步排查。
