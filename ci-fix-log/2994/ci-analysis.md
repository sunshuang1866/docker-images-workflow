# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常关闭
- 新模式症状关键词: `no builder`, `graceful_stop`, `closing transport`, `rpc error`, `Unavailable`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile 第 2/4 步，`dnf install` 阶段（Docker 构建层 #7）
- 失败原因: CI 的 BuildKit 构建器 `euler_builder_20260709_224657` 在 `dnf install` 下载仓库元数据过程中被优雅关闭（`graceful_stop`），导致构建连接中断。日志显示该构建器随后已不存在（`no builder found`），确认构建器实例已被销毁或重启。

### 与 PR 变更的关联
**无关**。PR 新增的 Dockerfile 内容完全正确，`dnf install` 命令语法和包名均有效。构建器关闭发生在 dnf 正常下载元数据阶段，属于 CI 基础设施（BuildKit builder）的运行实例被意外终止，与 Dockerfile 代码变更无因果关系。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。这是一个 CI 基础设施故障，应通过以下方式处理：
- 重新触发 CI pipeline（retry），大概率可以通过
- 若持续复现，需联系 CI 运维排查 BuildKit builder 在构建该镜像时频繁被终止的原因（可能是 runner 资源不足、超时策略过于激进，或调度器误判 builder 空闲而回收）

## 需要进一步确认的点
- 确认 BuildKit builder `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因（是否受 runner 资源配额限制、是否有外部调度回收策略）
- 若 retry 后仍失败，需获取 BuildKit builder 的系统日志（非 Docker build 日志）以确认 builder 实例终止的根因
- 可对比同一 CI runner 上其他成功构建的 job，排查是否为该 runner 特定时段的不稳定问题

## 修复验证要求
（不适用——此失败为 infra-error，无需修改代码文件。）
