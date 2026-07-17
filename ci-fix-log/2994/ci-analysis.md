# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: graceful_stop, no builder, closing transport, Unavailable, goaway, connection error, EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段，步骤 `#7 [2/4]`（`dnf install` 正在下载 OS 元数据时）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被提前终止（GOAWAY 帧携带 `graceful_stop` + `NO_ERROR`）。连接断开后，客户端无法找到该 builder，构建被迫中止。`graceful_stop` 表明这是一次计划内的优雅关闭（如超时、资源回收、调度器清理），而非 builder 自身崩溃。

日志中 `dnf install` 下载速度极慢（77 kB/s，2.8 MB 耗时 37+ 秒），可能是 builder 所在节点网络状况不佳，进而触发了 CI 调度器的超时回收机制。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及相应的元数据文件变更（README.md、image-info.yml、meta.yml），均为常规的添加新 OS 版本支持操作。Dockerfile 内容无语法错误或依赖缺失问题。失败的直接原因是 CI 基础设施层 BuildKit builder 实例被终止，属于 Jenkins + BuildKit 调度环境的稳定性问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 运行。** 这是典型的 CI 基础设施瞬时故障（builder 被提前回收），与 PR 代码无关。重新运行 CI Job 大概率可以通过。如果反复出现同一问题，则需排查 CI 环境中 `euler_builder_*` 实例的超时配置或网络质量。

## 需要进一步确认的点
- `dnf install` 下载速度仅 77 kB/s，需确认 CI builder 节点的网络出口是否存在带宽瓶颈或镜像站连通性问题。
- 确认 `euler_builder_*` builder 实例的存活时间（TTL）配置是否过短，导致长耗时构建（如从源码编译 Python 3.9.19）在完成前就被回收。
