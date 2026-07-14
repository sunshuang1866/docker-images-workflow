# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 构建器异常终止
- 新模式症状关键词: graceful_stop, no builder found, rpc error: Unavailable, connection error: EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`dnf install`），无具体行号
- 失败原因: CI 的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 镜像构建过程中被**外部关闭**（GOAWAY 帧携带 `graceful_stop` 调试数据，表明服务端主动发起优雅关闭）。构建器关闭后客户端无法找到该 builder，构建中断。此为 CI 基础设施层面问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**不相关。** PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套的 `README.md`、`image-info.yml`、`meta.yml` 元数据文件。构建失败发生在 `dnf install` 阶段（`[2/4]`），该阶段正在正常下载 openEuler 仓库元数据，并未报出任何包安装错误或命令执行错误——构建器在 `dnf` 正常执行过程中被外部终止。Dockerfile 内容本身不存在语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重新运行（re-run / re-trigger）。** 由于失败原因是 BuildKit 构建器实例被 CI 平台关闭（`graceful_stop`），属于临时性基础设施事件，最直接的处理方式是重新触发构建流水线。如果重新运后仍然失败，则需要 CI 平台运维排查 runner 节点资源或构建器生命周期管理策略。

## 需要进一步确认的点
- CI 平台是否存在构建器实例的存活时间（TTL）限制，导致 `dnf install` 耗时较长时构建器超时被回收。
- 构建日志显示 `dnf` 元数据下载速率仅 77 kB/s，是否存在网络拥塞导致构建窗口超出平台限制。建议对比同 runner 上其他成功构建的 `dnf` 下载速率。
