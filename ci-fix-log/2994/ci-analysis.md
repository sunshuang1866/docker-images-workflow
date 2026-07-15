# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: failed to receive status, rpc error, closing transport, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（即 `dnf install` 阶段），非 PR 代码文件内的行号错误
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 dnf 安装过程中被异常终止，RPC 传输通道关闭（`graceful_stop`），导致 `dnf install` 中断，后续因构建器实例已不存在（`no builder ... found`）无法恢复

### 与 PR 变更的关联
与本 PR 的代码变更**无直接关联**。PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`（一个标准 Dockerfile）、更新了 README、image-info.yml 和 meta.yml 元数据——这些都是纯文件级变更。Dockerfile 的 `dnf install` 步骤语法正确，构建在 dnf 下载元数据阶段（`OS 77 kB/s | 2.8 MB`）因构建器实例被回收/断开而中断，属 CI 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重新构建即可**。此失败为 BuildKit 构建器实例在构建中途被意外终止（`graceful_stop`），属于 CI 基础设施的瞬时故障或节点回收事件。PR 代码本身无需任何修改，直接重新触发 CI 流水线（retry）大概率可通过。

## 需要进一步确认的点
（日志已足够确定根因，无需进一步确认）
