# CI 失败分析报告

## 基本信息
- PR: #2983 — chore(fbthrift): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Agent通道断开
- 新模式症状关键词: ChannelClosedException, Unexpected termination of the channel, Remote call on ... failed, hudson.remoting

## 根因分析

### 直接错误

```
#11 2130.5 Writing cargo config for fbthrift to /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/build/fbthrift/source/thrift/lib/rust/.cargo/config.toml
FATAL: command execution failed
java.io.EOFException
Caused: java.io.IOException: Unexpected termination of the channel
Caused: hudson.remoting.ChannelClosedException: Channel "hudson.remoting.Channel@24d4cc0d:ecs-build-docker-x86-hk": Remote call on ecs-build-docker-x86-hk failed. The channel is closing down or has closed down
FATAL: Unable to delete script file /tmp/jenkins3161304096436833533.sh
```

### 根因定位
- 失败位置: Jenkins agent `ecs-build-docker-x86-hk`（在 Docker 构建第 11 步运行期间）
- 失败原因: Docker 构建执行到约 35 分钟后，Jenkins agent 与 master 之间的 remoting channel 意外断开（`EOFException` → `Unexpected termination of the channel` → `ChannelClosedException`）。日志最后一条有意义的构建输出是 "Writing cargo config for fbthrift"，表明构建仍在正常推进中，agent 通道中断是外部基础设施故障，并非构建代码本身的错误导致。

### 日志中的非致命信息
- `#11 725.2 fatal: not a git repository (or any of the parent directories): .git`：此错误发生在 boost/library 构建过程中（cmake 尝试 `git describe`），构建在此之后仍然继续推进（folly/fizz/mvfst/wangle 的 pinned rev 克隆均成功），**不是根因**。

### 与 PR 变更的关联
- **直接关联：低**。本次 PR 的变更（Dockerfile + `fix_getdeps.py`）不会直接导致 Jenkins agent 通道断开。通道断开最可能的原因是该 Docker 构建步骤从源码编译 boost + folly + fizz + mvfst + wangle + fbthrift，资源消耗大、耗时长（>35 分钟），可能触发 Jenkins agent 资源限制（OOM、磁盘满、或超时）导致 agent 进程异常退出。
- **间接关联：中**。`fix_getdeps.py` 中的 `_verify_hash` 正则 patch 可能存在匹配问题（见下方"潜在风险"），如果该 patch 实际未生效，后续 libaio 哈希校验失败可能导致错误重试或延长构建时间，间接加剧资源压力。

### 潜在风险：`fix_getdeps.py` 中 `_verify_hash` 正则匹配
第 2 步使用正则 patch `fetcher.py`：
```python
re.sub(
    r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )',
    'def _verify_hash(self):\n        pass',
    c2,
    flags=re.DOTALL
)
```
该正则使用 `\n    def ` 作为方法体结束的 lookahead 边界。存在以下风险：
1. **方法间有空行**：若 `_verify_hash` 方法与下一个 `def` 之间存在空行，`\n    def ` 无法匹配（实际是 `\n\n    def `），正则将吞入下一个方法的内容。
2. **方法前有装饰器**：若下一个方法有 `@staticmethod` 等装饰器，`\n    def ` 无法匹配（实际是 `\n    @staticmethod\n    def `），正则将扩展到更远。
3. **文件末尾的类成员**：若 `_verify_hash` 是类中最后一个方法，后面没有 `\n    def `，正则将完全不匹配，`re.sub` 返回原始字符串（即 patch 无效），哈希校验不会被跳过。

## 修复方向

### 方向 1（置信度: 低 — 重试重建）
由于失败类型为 `infra-error`（Jenkins agent 通道断开），建议先在 CI 中重新触发构建。如果构建在相同的第 11 步再次失败且 channel 意外关闭，则说明该构建对 agent 资源压力过大，需要优化构建流程（如分离依赖构建步骤、增加 agent 资源配额，或使用预编译的依赖镜像）或延长 Jenkins 超时时间。

### 方向 2（置信度: 中 — `fix_getdeps.py` 正则加固）
如果重试后构建继续进行但出现新的 libaio 哈希校验失败，则说明 `_verify_hash` patch 的正则未匹配成功。需要修改 `fix_getdeps.py` 中的正则表达式以准确匹配 `_verify_hash` 方法并替换为空实现。建议改为更稳健的策略：不使用正则替换方法体，而是直接用精确字符串替换将整个方法签名后的 return 语句改为 `pass`，或直接注释掉调用 `_verify_hash` 的位置。

## 需要进一步确认的点
1. **Jenkins agent 资源状态**：确认 `ecs-build-docker-x86-hk` agent 是否有内存/磁盘限制，是否配置了 build 超时时间。
2. **构建日志完整性**：日志在 `#11 525.7` 处因达到 2MiB 限制被截断（`[output clipped, log limit 2MiB reached]`），boost 编译的大量输出被丢弃，可能掩盖了真正触发 agent 崩溃的 OOM 或磁盘错误信息。需要获取完整未截断日志。
3. **libaio 预置 tarball 内部结构**：确认 `libaio-libaio-0.3.113.tar.gz` 解压后内部根目录名是否为 `libaio-0.3.113`（与 `fix_getdeps.py` 第 3 步修改的 `subdir` 一致）。如果实际目录名不同，构建后续步骤也会失败。

## 修复验证要求
若修复方向 2（正则加固）被采纳，code-fixer 在提交前必须：
1. 从 fbthrift `v2026.06.22.00` 的 `build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的实际签名和方法体，确认新正则能准确匹配全部内容且不侵入相邻方法。
2. 从 `build/fbcode_builder/getdeps/getdeps_platform.py` 确认 "openeuler" 字符串替换确实存在于目标行。
3. 验证 `libaio-libaio-0.3.113.tar.gz` 的实际内部目录结构与 manifest `subdir` 修改后的一致。
