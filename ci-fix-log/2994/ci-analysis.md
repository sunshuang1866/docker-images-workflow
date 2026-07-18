# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器异常终止
- 新模式症状关键词: closing transport due to, EOF, received prior goaway, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]` — `RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 dnf 安装系统依赖的过程中被异常终止（`graceful_stop`），导致 gRPC 连接断开（`EOF`），构建器随后不可用（`no builder found`）。这是 CI 基础设施层面的问题，与 PR 的 Dockerfile 内容无关。

### 与 PR 变更的关联
PR 变更仅为新增一个标准的 scann 1.4.2 Dockerfile（含 dnf 安装编译工具链、编译安装 Python 3.9.19、pip 安装 scann）、README 和 meta.yml 的条目更新。Dockerfile 内容本身无语法错误或逻辑问题——构建在 dnf 安装阶段尚未执行到任何可能因代码变更引发的失败步骤。该失败是 BuildKit 守护进程/构建器在 `euler_builder_20260709_224657` 实例上意外退出导致的 infra-error，与 PR 改动无关。

## 修复方向

### 方向 1（置信度: 高）
此失败为 CI 基础设施问题（BuildKit builder 异常终止），与 PR 代码变更无关。**无需修改 Dockerfile 或任何代码文件**。建议重新触发 CI 构建（retry），大概率在下一次构建中通过。

## 需要进一步确认的点
- 无需进一步确认。日志明确显示错误发生在 BuildKit 构建器连接层（gRPC transport closing / graceful_stop），而非 dnf 安装本身或后续构建步骤。
