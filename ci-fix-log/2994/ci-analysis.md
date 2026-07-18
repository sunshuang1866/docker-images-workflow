# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器被终止
- 新模式症状关键词: no builder found, graceful_stop, rpc error, Unavailable, EOF, buildkit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: 在运行时分配的 `euler_builder_20260709_224657` 构建器实例
- 失败原因: CI 使用的 BuildKit Docker 构建器（`euler_builder_20260709_224657`）在执行 Docker 构建步骤 `#7 [2/4] RUN dnf install ...`（下载 dnf 仓库元数据阶段）时被服务端主动关闭连接（`graceful_stop`），导致 BuildKit 客户端无法继续通信（`Received EOF`, `no builder found`）。这是一个纯粹的 CI 基础设施问题，构建器进程被意外终止。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 scann Dockerfile（安装基础编译工具 → 构建 Python 3.9.19 → pip 安装 scann）和配套的 README、image-info、meta 元数据更新。Dockerfile 内容正常，无语法错误、无异常依赖。构建失败发生在 `dnf install` 下载元数据的早期阶段，尚未执行到任何与 Dockerfile 内容实质相关的步骤。失败原因是 CI 构建器实例被基础设施服务端主动关闭。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 这是 CI 基础设施问题（BuildKit 构建器实例被终止），与 PR 代码无关。建议直接触发 CI 重试（如 `/retest` 或重新 push），等待 CI 分配一个稳定的构建器实例即可通过。

## 需要进一步确认的点
无。错误信息中 `graceful_stop` 明确指示构建器是被服务端主动终止的，属于基础设施层面的操作，与本次 PR 的 Dockerfile 内容无关。
