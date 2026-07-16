# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder意外终止
- 新模式症状关键词: no builder found, graceful_stop, closing transport, rpc error, Unavailable, buildkit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
...
Finished: FAILURE
```

### 根因定位
- 失败位置: Dockerfile `RUN dnf install ...` 步骤（BuildKit 构建步骤 `#7 [2/4]`）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 `dnf install` 执行约 38 秒后意外终止（`graceful_stop` + `NO_ERROR` goaway），导致 Docker 构建因 builder 不可用而失败。该错误与 PR 代码变更无关，属于 CI 基础设施层面的问题（builder 被系统回收或节点资源不足导致连接断开）。

### 与 PR 变更的关联
**无关。** PR 仅新增了 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（meta.yml、README.md、image-info.yml）。构建失败发生在 Dockerfile 第一个 `dnf install` 步骤中，且错误为 BuildKit builder 被意外终止，并非 `dnf` 命令本身的错误。Dockerfile 本身的语法和内容没有明显问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 运行。** 这是 BuildKit builder 实例被 CI 基础设施意外回收导致的瞬态故障，通常重试即可成功。Code Fixer 无需对 PR 代码做任何修改。

## 需要进一步确认的点
- BuildKit builder 终止的具体原因（资源不足、节点驱逐、超时等），需查看 CI 平台侧（Jenkins 节点管理日志 / BuildKit daemon 日志）确认。
- 若多次重试均在相同位置失败，则需排查该 `dnf install` 命令是否触发了 OOM Killer 导致 builder 被终止。
