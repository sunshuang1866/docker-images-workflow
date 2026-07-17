# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器丢失
- 新模式症状关键词: `failed to receive status`, `rpc error`, `closing transport`, `graceful_stop`, `no builder found`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile `RUN dnf install -y ...` 步骤（构建步骤 #7 [2/4]）
- 失败原因: Docker 构建的 BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install`（下载 OS 仓库元数据阶段，已耗时约 38 秒，速度仅 77 kB/s）时被远程终止（gRPC `graceful_stop`），导致构建连接丢失，构建失败。与 PR 代码变更无关，属于 CI 基础设施问题。

### 与 PR 变更的关联
PR 新增了 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（meta.yml、README.md、image-info.yml）。所涉及的 Dockerfile 语法和 `dnf install` 依赖包列表均正确无误，构建失败发生在 `dnf install` 下载仓库元数据的中途（非命令本身报错），根因是 BuildKit builder 被意外回收/关闭，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试**。该失败为 CI 基础设施的瞬时故障（BuildKit builder 在构建过程中因未知原因被 `graceful_stop`），与代码无关。重新触发一次 CI 构建即可验证——若新构建在相同步骤成功完成，则确认本次为 infra-error。

## 需要进一步确认的点
- CI 平台的 BuildKit builder 是否有最大执行时间限制（如 1 小时），以及本次构建的 builder `euler_builder_20260709_224657` 是否因超时被回收。
- `dnf install` 步骤中 OS 仓库元数据下载速度仅 77 kB/s 是否正常——若该速度持续偏低，可能触发 builder 超时回收机制。
- 若重试后仍然失败，需要确认是否为该 builder 节点（`ecs-build-docker-x86-hk`）的特定问题（考虑重调度到其他节点）。
