# CI 失败分析报告

## 基本信息
- PR: #2983 — chore(fbthrift): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Jenkins Agent 通道断开
- 新模式症状关键词: ChannelClosedException, EOFException, Remote call failed, channel is closing down

## 根因分析

### 直接错误
```
FATAL: command execution failed
java.io.EOFException
	at java.base/java.io.ObjectInputStream$PeekInputStream.readFully(Unknown Source)
	...
Caused: java.io.IOException: Unexpected termination of the channel
	at hudson.remoting.SynchronousCommandTransport$ReaderThread.run(SynchronousCommandTransport.java:80)
Caused: hudson.remoting.ChannelClosedException: Channel "hudson.remoting.Channel@24d4cc0d:ecs-build-docker-x86-hk": Remote call on ecs-build-docker-x86-hk failed. The channel is closing down or has closed down
	at hudson.remoting.Channel.call(Channel.java:1101)
	...
FATAL: Unable to delete script file /tmp/jenkins3161304096436833533.sh
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: Jenkins 基础设施（非代码层面）
- 失败原因: Jenkins Master 与远程构建节点 `ecs-build-docker-x86-hk` 之间的 remoting 通道意外断开（`ChannelClosedException`），导致命令执行中断并标记为失败

### 与 PR 变更的关联
此次失败与 PR 代码变更**无关**。Docker 构建在通道断开前已正常运行超过 2130 秒（约 35 分钟），推进到以下阶段：
- Boost 头文件安装完成（~525s）
- folly 依赖拉取完成（~901s）
- fizz 依赖拉取完成（~1390s）
- mvfst 依赖拉取完成（~1606s）
- wangle 依赖拉取完成（~2017s）
- fbthrift Cargo config 写入中（~2130s）

构建流程在正常进行中因 Jenkins Agent 通道断开而失败，未观察到任何编译错误、依赖解析失败或测试失败。日志中出现的 `fatal: not a git repository`（#11 725.2）为 Docker 构建内部的非致命警告，构建在此之后继续运行了约 1400 秒无异常。

## 修复方向

### 方向 1（置信度: 中）
**重试 CI 构建**。`ChannelClosedException` 通常由 Jenkins Agent 节点网络波动、节点资源耗尽（OOM / 磁盘满）或 Agent 进程异常退出引起，属于瞬时基础设施故障。重新触发 CI 流水线大概率可通过。

## 需要进一步确认的点
1. Jenkins 节点 `ecs-build-docker-x86-hk` 在构建期间是否存在资源耗尽（内存、磁盘）或网络中断的记录
2. 日志在 `[output clipped, log limit 2MiB reached]` 处被截断，截断区域（#11 525s ~ #11 725s 之间）是否包含构建错误无法确认。需获取完整未截断日志以排除 Docker 构建内部的实际错误
3. 若有多次重试均失败，需检查是否因 fbthrift 全量编译（boost + folly + fizz + mvfst + wangle + fbthrift）导致构建耗时过长触发了 CI 超时限制
