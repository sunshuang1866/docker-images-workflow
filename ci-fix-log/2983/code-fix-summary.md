# 修复摘要

## 修复的问题
无需代码修改。CI 失败类型为 `infra-error`（Jenkins agent 通道意外断开），非代码 bug 导致。

## 修改的文件
无（infra-error，无需代码修改）。

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`。Docker 构建执行到约 35 分钟时（最后输出为 "Writing cargo config for fbthrift"），Jenkins agent `ecs-build-docker-x86-hk` 与 master 之间的 remoting channel 意外断开（`EOFException` → `ChannelClosedException`）。构建本身在正常推进中，agent 通道中断是外部基础设施故障（可能由 OOM、磁盘满或超时触发）。

根据修复原则，`infra-error` 不应通过修改代码来绕过，建议在 CI 中重新触发构建。如重试后仍失败，需从基础设施层面排查（增加 agent 资源配额、延长超时时间、或分离构建步骤）。

### 附加验证（按分析报告要求）

按报告要求对 `fix_getdeps.py` 中的正则 patch 进行了上游源码验证（tag: `v2026.06.22.00`）：

1. **`_verify_hash` 正则**：已从上游 `https://raw.githubusercontent.com/facebook/fbthrift/v2026.06.22.00/build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的实际签名 `def _verify_hash(self) -> None:`，用 Python 运行正则确认匹配成功，patch 正确替换方法体为空实现，不侵入下游 `_download_dir` 方法。当前正则有效。

2. **`getdeps_platform.py` 字符串替换**：已确认上游源文件中 `"fedora", "centos", "centos_stream", "rocky", "alma"` 精确存在于目标行（`get_package_manager` 方法中），`str.replace` 可正确匹配。

3. **libaio tarball 内部结构**：无法在不实际解压的情况下验证 `libaio-libaio-0.3.113.tar.gz` 内部目录名，但二进制文件本身不在本次 PR 变更范围内。

## 潜在风险
无。未修改任何代码。