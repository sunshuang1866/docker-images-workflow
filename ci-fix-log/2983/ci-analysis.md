# CI 失败分析报告

## 基本信息
- PR: #2983 — chore(fbthrift): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Agent通道断开
- 新模式症状关键词: ChannelClosedException, EOFException, Unexpected termination of the channel, ecs-build-docker-x86-hk

## 根因分析

### 直接错误

构建推进到 fbthrift 本身的 cargo config 写入阶段时，Jenkins agent 与 master 的连接通道意外断开：

```
#11 2130.5 Writing cargo config for fbthrift to /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/build/fbthrift/source/thrift/lib/rust/.cargo/config.toml
FATAL: command execution failed
java.io.EOFException
	at java.base/java.io.ObjectInputStream$PeekInputStream.readFully(Unknown Source)
	...
Caused: java.io.IOException: Unexpected termination of the channel
Caused: hudson.remoting.ChannelClosedException: Channel "hudson.remoting.Channel@24d4cc0d:ecs-build-docker-x86-hk": Remote call on ecs-build-docker-x86-hk failed. The channel is closing down or has closed down
	at hudson.remoting.Channel.call(Channel.java:1101)
	...
FATAL: Unable to delete script file /tmp/jenkins3161304096436833533.sh
java.io.EOFException
	...
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位

- 失败位置: Docker build step #11（`getdeps.py build fbthrift`），运行时约 35 分钟后
- 失败原因: Jenkins agent `ecs-build-docker-x86-hk` 与 master 的 remoting channel 被意外关闭，导致正在执行的 Docker 构建命令被强制终止。

**两种可能的底层原因：**

1. **构建超时（可能性较高）**：fbthrift 及其全部 C++ 依赖（boost、folly、fizz、mvfst、wangle）在一个 `RUN` 指令中从源码完整编译，极其耗时。日志中步骤 #11 已运行超过 2130 秒（约 35 分钟）时仍在进行依赖构建，而 boost header 拷贝（第 525 秒）到 cargo config 写入（第 2130 秒）之间耗时约 26 分钟，构建远未完成。若 Jenkins job 超时配置（如 30 或 60 分钟）不足以容纳完整编译，master 端将在超时后强制断开 agent 连接，导致 `ChannelClosedException`。

2. **Agent 资源耗尽（可能性较低但不可排除）**：编译 boost + folly + fizz + mvfst + wangle + fbthrift 全量依赖链对内存和磁盘的需求极大。若 CI runner 的资源配置不足以支撑此编译负载，agent 进程可能因 OOM killer 或磁盘满而崩溃，引发 channel 异常关闭。

### 日志中的非致命信息

```
#11 725.2 fatal: not a git repository (or any of the parent directories): .git
```

此行出现在依赖构建阶段（boost header 拷贝与 folly pinned rev 输出之间），来自 getdeps 在 tarball 解压的依赖目录中尝试获取 git 版本信息时产生的非致命警告。构建在此之后继续推进到 #11 2130 秒，证明该行并非根因。

### 与 PR 变更的关联

PR 新增了 `Others/fbthrift/2026.06.22.00/24.03-lts-sp4/` 目录（Dockerfile、fix_getdeps.py、libaio tarball）。构建流程本身在正常推进——依次处理了 libaio、boost、folly、fizz、mvfst、wangle 等依赖——表明 Dockerfile 和 fix_getdeps.py 的逻辑在执行层面可能是正确的。失败发生在构建过程的资源/超时维度，而非代码逻辑维度。

## 修复方向

### 方向 1（置信度: 中）
**增加 CI job 超时配置**。fbthrift 的全量依赖链从源码编译天然耗时极长。检查 Jenkins job 的超时设置，若当前限制不足以完成完整构建，需为 fbthrift 构建 job 单独放宽超时阈值。同时可考虑将依赖编译拆分为多个 Docker layer（如将 boost 的下载和编译独立为一个 `RUN` 步骤），以便利用 Docker 层缓存避免重复编译。

### 方向 2（置信度: 低）
**提升 CI runner 规格**。确认 `ecs-build-docker-x86-hk` 的内存和磁盘配置是否满足编译 boost + folly 全套依赖链的最低要求。如不足，需为 fbthrift 构建分配更高规格的 runner，或通过 `--parallelism` 参数限制 getdeps 的并行编译数以降低瞬时资源峰值。

### 方向 3（置信度: 低）
**fix_getdeps.py 正则可能未生效**。`fix_getdeps.py:17-22` 中的正则 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` 用于替换 `fetcher.py` 中的 `_verify_hash` 方法体。若 fbthrift v2026.06.22.00 中该方法的实际签名与此正则不匹配，替换将静默失败（不报错但也不生效），导致后续依赖下载阶段 hash 校验失败。但日志显示构建已走到 folly/fizz/mvfst/wangle 阶段，因此此风险较低。

## 需要进一步确认的点

1. **获取 Jenkins job 的超时配置**，确认是否因超时触发了 channel 关闭。
2. **获取 `ecs-build-docker-x86-hk` agent 的系统日志**（dmesg/journalctl 中 OOM killer 记录、`df -h` 磁盘使用情况），确认是否因资源耗尽导致 agent 进程崩溃。
3. **对比同一 PR 在 aarch64 架构上的构建结果**（若 CI 有对应的 aarch64 job）。若 aarch64 也不同形式失败，可交叉验证是代码问题还是资源/超时问题。
4. **确认 Jenkins master 日志**中是否有关于 `ecs-build-docker-x86-hk` 断开连接的更多上下文（如 idle timeout、agent 自检失败等）。

## 修复验证要求（仅当修复涉及 fix_getdeps.py 正则时填写）

若修复方向 3 被采纳，code-fixer 必须从 fbthrift v2026.06.22.00 的 `build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的实际函数签名，确认 `fix_getdeps.py` 中的正则 `def _verify_hash\(self[^)]*\)[^:]*:.*?` 确实能匹配该签名后再提交修改。
