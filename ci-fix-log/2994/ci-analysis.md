# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, Unavailable, EOF

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7 `[2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`（Dockerfile 第 7 行附近）
- 失败原因: CI 的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 镜像构建过程中被主动终止（graceful_stop），导致与构建器的连接断开，构建流程无法继续。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 新增的 Dockerfile 内容为标准的应用镜像构建流程（dnf 安装编译依赖 → 编译安装 Python 3.9.19 → pip 安装 scann），语法正确、逻辑完整。失败发生在 dnf 下载系统软件包元数据阶段（此时下载速度仅 77 kB/s，耗时约 37 秒），属于 CI 基础设施层面的构建器生命周期管理问题，非代码触发的失败。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施问题，无需修改 PR 代码。** 该失败是 BuildKit 构建器实例在构建过程中被意外回收/终止所致（`graceful_stop` 关键字表明是有意终止而非崩溃）。建议：
1. 直接触发 CI 重试（re-run），大概率可正常通过。
2. 若重试后仍失败，需排查 CI 构建节点的 BuildKit 超时配置或构建器实例存活策略。

## 需要进一步确认的点
- 无需进一步确认。日志证据明确指向 BuildKit 基础设施级别的构建器连接中断，与 PR 新增的 Dockerfile 内容无关。
