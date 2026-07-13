# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：Docker 构建进程在运行 ~35 分钟后被 Jenkins runner 异常终止（ChannelClosedException / Unexpected termination of the channel），无任何代码编译错误。

## 修改的文件
无代码修改。

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`（置信度: 中），根因是 fbthrift 全量源码编译（通过 getdeps.py）极其耗时，在 2C/4G runner 上仅依赖解析/准备阶段就用了 35+ 分钟，触发 Jenkins job 超时或 OOM Killer。日志中无任何编译错误、依赖缺失或代码层面的错误。

对 `fix_getdeps.py` 的正则进行了上游验证：已从 fbthrift `v2026.06.22.00` 获取 `build/fbcode_builder/getdeps/fetcher.py`，确认 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` 正则与上游 `_verify_hash` 方法签名完全匹配，替换成功。代码层面无问题。

建议措施（需 CI 管理员操作，非代码修改）：
1. 增大 runner 规格（内存 ≥ 8G，建议 16G）
2. 延长 Jenkins job timeout（≥ 4 小时）
3. 检查是否可通过多阶段构建或使用预编译包减少构建时间

## 潜在风险
无。此为基础设施配置问题，不影响代码正确性。