# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器意外终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, Unavailable, EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 第 7 步（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`），执行约 38.6 秒时
- 失败原因: Docker BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 下载 openEuler 仓库元数据期间被意外终止（graceful_stop），导致 gRPC 连接断开，后续操作无法找到该构建器。这是一次 CI 基础设施故障，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。PR 新增的 Dockerfile 内容语法正确、逻辑合理（安装构建依赖 → 编译 Python 3.9 → pip 安装 scann），构建于第 2 步（安装系统包 dnf）即已中断，尚未进入任何 PR 特有的编译或安装逻辑。该构建器在同一个 dnf 阶段即被终止，说明是在执行通用系统包安装命令时遭遇基础设施问题，而非 PR 代码触发了构建失败。

## 修复方向

### 方向 1（置信度: 高）
**无需修复**。失败原因为 CI 基础设施问题（BuildKit 构建器被意外终止），Dockerfile 本身没有错误。Code Fixer 无需对 PR 代码做任何修改。建议重新触发 CI 流水线重跑即可。

## 需要进一步确认的点
- 无需进一步确认。日志清晰表明构建器在 `dnf install` 阶段被 `graceful_stop`，属于典型的基础设施中断，与 PR 代码质量无关。
