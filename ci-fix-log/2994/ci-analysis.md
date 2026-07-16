# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 丢失
- 新模式症状关键词: `rpc error: code = Unavailable`, `closing transport`, `graceful_stop`, `no builder`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段，Run #7（`dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被提前终止。日志中 `graceful_stop` 和 `NO_ERROR` 表明 builder 收到了正常的关闭信号（非崩溃），极可能是 CI 基础设施的 timeout 或资源管理操作导致 builder 进程被回收。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 内容正确，语法无误（BuildKit 成功解析 Dockerfile 并执行到第 7 步）。构建在 `dnf install` 下载 openEuler 包元数据阶段因 BuildKit builder 实例意外消失而中断，属于 CI 基础设施故障，非 Dockerfile 或代码问题。

## 修复方向

### 方向 1（置信度: 低）
**重试 CI 构建。** 这是 BuildKit builder 基础设施的一次性故障（builder 被提前回收），与 PR 代码无关。建议重新触发 CI 流水线重试，大概率会正常通过。

## 需要进一步确认的点
- CI 构建环境是否有超时限制导致 builder 在长时间 dnf 下载期间被终止（日志显示 dnf 下载约 38 秒后被 kill）
- BuildKit builder pool 是否有最大存活时间限制
- 本次构建是否与 CI 基础设施维护窗口冲突
- 需确认同一 PR 在重试后的构建结果，以排除偶发性故障

## 修复验证要求
无需验证（infra-error，无代码修复）。
