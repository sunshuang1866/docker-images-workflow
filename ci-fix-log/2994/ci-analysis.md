# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 构建器异常终止
- 新模式症状关键词: graceful_stop, rpc error: code = Unavailable, closing transport, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`，第一个 `RUN dnf install ...` 步骤（Docker BuildKit step #7 [2/4]）
- 失败原因: Docker BuildKit 构建器实例 `euler_builder_20260709_224657` 在 `dnf install` 下载仓库元数据期间被异常终止（收到 `graceful_stop` 信号后连接断开，随后构建器实例不可用）。该错误与 PR 代码无关，属于 CI 基础设施层面的 BuildKit 构建器运行时故障。

### 与 PR 变更的关联
**无关。** PR 新增的 Dockerfile 中 `dnf install` 命令语法正确、包名有效，属于标准构建流程。BuildKit 构建器在 DNF 下载元数据约 38 秒时被外部原因终止，并非由此 Dockerfile 的内容触发。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是 CI 基础设施的 BuildKit 构建器运行时故障（构建器实例在构建过程中被异常关闭），属于瞬态问题，大概率重新运行即可通过。若反复出现同类错误，需由 CI 平台运维排查 BuildKit 构建器节点（`ecs-build-docker-x86-hk`）的健康状态和资源使用情况。

## 需要进一步确认的点
- BuildKit 构建器 `euler_builder_20260709_224657` 被 `graceful_stop` 终止的具体原因（如节点资源耗尽、OOM、人工干预、调度策略等），需 CI 平台运维从构建器节点日志中确认。
- DNF 下载速度仅 77 kB/s（下载 2.8 MB 元数据耗时 37+ 秒），若为网络拥塞继发超时导致构建器被回收，建议检查 CI 节点与 openEuler 镜像仓库之间的网络状况。

## 修复验证要求
无需验证——此错误为 infra-error，与代码无关，无需 code-fixer 修改任何文件。重新触发 CI 构建即可。
