# 修复摘要

## 修复的问题
CI 失败原因为 `infra-error`：Jenkins 远程代理节点 `ecs-build-docker-x86-hk` 在执行长时间 Docker 构建（35+ 分钟）时通道意外断连（`java.io.EOFException` → `ChannelClosedException`），属于基础设施问题，非代码缺陷。

## 修改的文件
无代码修改。

## 修复逻辑
根据 CI 失败分析报告，本次失败的直接原因是 Jenkins master 与远程构建节点之间的 remoting 通道断开。Docker 构建自身在断连前进展正常（已完成 boost 安装、folly/fizz/mvfst/wangle 依赖解析，正在生成 fbthrift Rust cargo 配置），无编译错误输出。该问题属于基础设施故障，建议重试 CI 观察是否稳定复现。分析报告将失败类型明确标注为 `infra-error`，按照规范无需进行代码修改。

## 潜在风险
如果重试后仍然失败，需进一步排查：
1. Jenkins 节点 `ecs-build-docker-x86-hk` 的资源使用情况（OOM、磁盘满等）
2. `fix_getdeps.py` 中跳过 `_verify_hash` 的正则表达式是否在目标版本 fbthrift (`v2026.06.22.00`) 的 `fetcher.py` 中成功匹配（分析报告标注置信度低）
3. 是否需在 Dockerfile 中为 `getdeps.py` 添加 `--num-jobs` 参数限制并行编译数以减少峰值内存