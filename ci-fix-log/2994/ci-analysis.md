# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 崩溃
- 新模式症状关键词: graceful_stop, closing transport, connection error: EOF, no builder found, buildkit, rpc error: code = Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: 构建步骤 `[2/4]`（dnf install 阶段，约第 38 秒处）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 `dnf install` 下载仓库元数据时收到 `graceful_stop` 信号后意外终止，导致 gRPC 连接断开（`closing transport due to: connection error: EOF`），后续构建步骤无法找到该 builder。

## 与 PR 变更的关联

**与 PR 无关。** 该失败是 CI 基础设施层面的 BuildKit daemon 崩溃。

- BuildKit builder 在正常执行 `RUN dnf install`（安装 gcc、gcc-c++、make、wget 等标准编译工具链）的过程中被 `graceful_stop` 信号终止。
- PR 新增的 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）语法正确，所安装的包均为 openEuler 24.03-LTS-SP4 标准仓库中的合法软件包（gcc、gcc-c++、make、wget、openssl-devel、bzip2-devel、zlib-devel），不存在会导致 BuildKit 崩溃的非法指令或依赖错误。
- 构建失败发生在第一步 `dnf install` 的元数据下载阶段（约第 38 秒），尚未到达 `wget Python`、`./configure && make` 或 `pip install scann` 等后续步骤，失败点早于任何与 PR 特有内容相关的逻辑。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 该失败为 CI 基础设施问题（BuildKit builder 意外终止），与 PR 代码变更无关。建议触发 CI 重试（re-run / re-trigger）以确认构建能否正常通过。若多次重试仍复现，需排查 CI 基础设施：
- BuildKit daemon / Docker 宿主机是否存在资源压力（内存不足触发 OOM Kill）
- CI 节点是否在构建期间发生驱逐或维护操作
- 是否存在编排层超时配置过短导致 BuildKit builder 被提前回收

## 需要进一步确认的点
- BuildKit builder 进程被 `graceful_stop` 终止的具体原因：是否为 CI 编排层面的超时、资源限制触发 OOM Kill、或节点调度/驱逐。
- 若重试后问题消失，则确认为临时性基础设施抖动，无需额外处理。
- 若重试后持续失败，需获取 CI runner 宿主机的系统日志（dmesg/syslog）确认 OOM Killer 或 docker daemon 异常。
