# CI 失败分析报告

## 基本信息
- PR: #2983 — chore(fbthrift): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Jenkins Agent 连接中断
- 新模式症状关键词: ChannelClosedException, EOFException, Remote call failed, channel is closing down, ecs-build-docker

## 根因分析

### 直接错误
```
FATAL: command execution failed
java.io.EOFException
  at java.base/java.io.ObjectInputStream$PeekInputStream.readFully(Unknown Source)
  ...
Caused: java.io.IOException: Unexpected termination of the channel
  at hudson.remoting.SynchronousCommandTransport$ReaderThread.run(...)
Caused: hudson.remoting.ChannelClosedException: Channel "hudson.remoting.Channel@24d4cc0d:ecs-build-docker-x86-hk": Remote call on ecs-build-docker-x86-hk failed. The channel is closing down or has closed down
  at hudson.remoting.Channel.call(Channel.java:1101)
  ...
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: Jenkins agent `ecs-build-docker-x86-hk`（远程构建节点）
- 失败原因: Jenkins agent 与 master 之间的 remoting 通道意外关闭（EOFException → ChannelClosedException），导致正在执行的 shell 步骤（Docker build）被强制终止。此时 Docker 构建本身并未报错，正在正常推进 getdeps 依赖链。

### 与 PR 变更的关联
**本次 PR 变更不是失败原因。** Docker 构建日志显示构建按预期推进：
1. 系统包安装（dnf install）— 正常完成
2. `fix_getdeps.py` 补丁执行（openEuler 发行版识别、libaio hash 跳过、manifest subdir 修正）— 正常
3. Boost 编译安装 — 正在进行中（日志在 2MiB 处被截断）
4. folly / fizz / mvfst / wangle 依赖解析（Using pinned rev）— 正常
5. fbthrift cargo config 写入 — 正在执行（#11 2130.5 秒，约 35.5 分钟）

构建在正常运行约 35.5 分钟时因 Jenkins agent 通道断开而中断，未出现任何从 Docker 构建内部产生的编译错误、链接错误或测试失败。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建**。这是一次性的 Jenkins 基础设施故障（agent 连接中断），与代码变更无关。重新运行该 job 大概率可以成功通过。

### 方向 2（置信度: 低）
**排查 agent 资源或网络问题**。如果多次重新触发均在同一阶段失败，则可能是：
- Agent `ecs-build-docker-x86-hk` 内存不足（OOM），Docker 构建 boost + folly 等大型 C++ 项目时内存压力大
- CI job 配置的构建超时时间不足（当前构建至少需要 35+ 分钟，尚不清楚完成总共需要多长时间）
- Agent 与 master 之间的网络不稳定

## 需要进一步确认的点
1. **下游架构 job 日志**：当前提供的日志来自触发/编排层 job（x86 构建的主 job），若 PR 仍标记为 `ci_failed` 且重新触发后仍失败，需要获取该 job 的完整未截断日志（当前 2MiB 截断可能丢失了后续的错误信息）。
2. **构建总耗时**：fbthrift 的 getdeps 完整构建（boost + folly + fizz + mvfst + wangle + fbthrift + 测试）需要多少时间？如果超过 CI 配置的超时阈值，需考虑增大超时或优化构建（如通过 dnf 安装部分预编译依赖替代源码编译）。
3. **fix_getdeps.py 正则健壮性**：`_verify_hash` 方法的 patch 正则 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` 依赖上游 `fetcher.py` 的特定方法签名格式和缩进风格。若上游代码中 `_verify_hash` 的签名格式变化（如多行参数、类型注解换行、该方法是类中最后一个方法导致无后续 `def`），正则可能匹配失败，导致 hash 校验未被跳过，构建将在 libaio 步骤失败。当前日志未覆盖到该环节，无法验证正则是否实际匹配成功。

## 修复验证要求
若 code-fixer 需要调整 `fix_getdeps.py` 中的正则，必须从 fbthrift v2026.06.22.00 的 `build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的实际签名，验证正则确实能匹配目标内容后再提交。同时验证 `fetcher.py` 的缩进风格（4 空格 vs tab）与正则中的 `\n    def ` 一致。
