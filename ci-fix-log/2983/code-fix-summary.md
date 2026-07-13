# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），Jenkins agent 与 master 的 remoting channel 意外断开导致构建中断。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告确认失败类型为 `infra-error`，根因如下：

1. **直接原因**：Jenkins agent `ecs-build-docker-x86-hk` 在执行 `getdeps.py build fbthrift`（Docker build step #11）约 35 分钟后，与 master 的 remoting channel 被意外关闭，抛出 `ChannelClosedException`。

2. **底层原因**：fbthrift 的全量 C++ 依赖链（boost、folly、fizz、mvfst、wangle）在一个 `RUN` 指令中从源码完整编译，极为耗时。日志显示构建在依赖编译阶段（cargo config 写入）已运行超过 2130 秒且远未完成。很可能是 Jenkins job 的超时配置不足以容纳完整编译，或 agent 资源（内存/磁盘）不足。

3. **代码正确性**：日志显示构建流程正常推进，依次处理了 libaio、boost、folly、fizz、mvfst、wangle 等依赖，表明 Dockerfile 和 fix_getdeps.py 的逻辑在执行层面是正确的。失败发生在资源/超时维度，而非代码逻辑维度。

根据"infra-error 不做代码修改"的原则，此 PR 的代码无需改动。需由 CI 运维侧处理：
- 检查并放宽 Jenkins job 的超时配置
- 或提升 CI runner 的资源配置（内存/磁盘）

## 潜在风险
无（未修改任何代码）