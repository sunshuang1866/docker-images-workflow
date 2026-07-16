# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器崩溃
- 新模式症状关键词: no builder found, closing transport due to connection error, EOF, graceful_stop

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`dnf install` 下载仓库元数据阶段）
- 失败原因: CI 基础设施中的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 期间崩溃或失去连接（`EOF` + `graceful_stop`），导致 Docker 构建进程无法继续，整个 job 被标记为 `FAILURE`。

### 与 PR 变更的关联
PR 变更与此次失败**无关**。PR 仅新增了一个标准的 Dockerfile（安装 gcc/gcc-c++/make/wget/openssl-devel/bzip2-devel/zlib-devel、编译 Python 3.9.19、pip 安装 scann），以及对应的 README、image-info、meta 元数据条目。Dockerfile 语法正确，`dnf install` 命令参数合法。构建在 dnf 下载仓库元数据阶段（`#7 38.59 OS` — 约 38.59 秒处）因构建器崩溃而中断，尚未执行到任何与 PR 代码逻辑相关的步骤。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。此次失败为 BuildKit 构建器实例的瞬态基础设施故障（连接丢失、构建器消失），与代码变更无关。绝大多数情况下，重试即可通过。

## 需要进一步确认的点
- CI 环境中 BuildKit 构建器 `euler_builder_20260709_224657` 为何会被终止（graceful_stop），可能与 runner 资源配额、构建器超时策略或节点调度有关。如果重试后仍然失败，需要排查 CI 基础设施侧的 BuildKit 守护进程日志。
