# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 意外终止
- 新模式症状关键词: graceful_stop, no builder found, rpc error, closing transport, EOF, buildkit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile 第 7 行 `RUN dnf install -y ...`（构建步骤 [2/4]）
- 失败原因: CI 构建使用的 BuildKit `docker-container` driver 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被意外终止（goaway `graceful_stop`），gRPC 连接断开，导致 Docker 构建失败。该错误与 PR 代码变更无关。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile（安装 gcc/gcc-c++/make/wget 及 openssl-devel/bzip2-devel/zlib-devel 等常用包，构建 Python 3.9.19 并安装 scann），语法正确，包名均为 openEuler 仓库标配。失败发生在 BuildKit builder 进程级别——builder 容器/守护进程在 `dnf` 下载仓库元数据时被终止（"graceful_stop"），`dnf` 自身未产出任何包缺失或安装失败的错误。日志中 `dnf` 正在以 77 kB/s 的极慢速度下载 2.8 MB 元数据，耗时已超 37 秒，存在因网络过慢触发 CI 超时机制的嫌疑，但确切终止原因（OOM / 超时 / runner 资源回收）无法从当前日志确定。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 这是 CI 基础设施问题（BuildKit builder 进程被终止），与 PR 中 Dockerfile 的正确性无关。应重新触发 CI 构建，若重试后通过则确认根因为 infra 波动；若持续失败在同一位置，则需排查 CI runner 的网络状况或构建超时配置。

## 需要进一步确认的点
- BuildKit builder 容器 `euler_builder_20260709_224657` 的终止原因：是 runner 内存不足 OOM-kill、构建超时（dnf 阶段网络极慢）、还是 runner 资源调度回收。需要查看 CI runner 的系统日志（dmesg / journalctl）确认。
- 若重试后仍然失败，需确认 `openeuler/openeuler:24.03-lts-sp4` 基础镜像中 dnf 仓库默认配置的网络可达性（日志中 dnf 下载 repo 元数据速度仅 77 kB/s，异常缓慢）。
- 对比同 runner 上其他成功构建的 dnf 阶段耗时，判断是否为本次构建特有网络波动。

## 修复验证要求
无需修复验证。此失败类型为 `infra-error`，Code Fixer 无需处理。
