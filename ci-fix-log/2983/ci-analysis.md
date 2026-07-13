# CI 失败分析报告

## 基本信息
- PR: #2983 — chore(fbthrift): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高（根因类型） / 低（具体触发原因）
- 知识库匹配: 新模式
- 新模式标题: Jenkins Agent 断连
- 新模式症状关键词: `ChannelClosedException`, `EOFException`, `Remote call failed`, `channel is closing down`, `ecs-build-docker`

## 根因分析

### 直接错误
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
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: 无法精确确定（Docker 构建步骤 `#11 RUN ... getdeps.py build fbthrift` 执行期间）
- 失败原因: Jenkins Agent（`ecs-build-docker-x86-hk`）在执行 Docker 构建时通道意外关闭（`ChannelClosedException` / `EOFException`），构建被强制中断。Docker 构建步骤 #11 已运行超过 2100 秒（约 35 分钟），日志因超过 2MiB 限制被截断，可能掩盖了构建内部的真实错误，也可能仅仅是资源/超时导致 Jenkins 节点断连。

### 与 PR 变更的关联
PR 变更（新增 `Dockerfile`、`fix_getdeps.py`、`libaio tarball`）是构建的触发者，但其代码改动本身不直接引发 Jenkins Agent 断连。然而，以下 PR 改动存在**潜在风险**，可能间接导致构建耗时过长或内部失败：

1. **`fix_getdeps.py` 中 `_verify_hash` 的正则替换可能未命中**：脚本使用 `re.sub` 匹配 `fetcher.py` 中的 `def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )`，如果 fbthrift v2026.06.22.00 的 `fetcher.py` 中 `_verify_hash` 方法签名与此正则不匹配（如参数名不是 `self`、方法有装饰器、或该方法是类的最后一个方法导致不存在后续 `\n    def `），则 `re.sub` 返回原字符串不变，哈希校验跳过逻辑未生效，getdeps 将尝试自行下载并校验 libaio，增加构建耗时或失败概率。

2. **`fix_getdeps.py` 中 manifest subdir 与预置 tarball 内部目录可能不一致**：脚本将 `subdir = libaio-libaio-0.3.113` 改为 `subdir = libaio-0.3.113`，若预置的 `libaio-libaio-0.3.113.tar.gz` 内部解压目录为 `libaio-libaio-0.3.113` 而非 `libaio-0.3.113`，则 getdeps 提取后因目录名不匹配而失败。

3. **日志中部被截断**：`#11 [output clipped, log limit 2MiB reached]` 表明构建日志超过 2MiB 被截断，可能丢失了内部真实错误信息。

## 修复方向

### 方向 1（置信度: 中）
**修复 `fix_getdeps.py` 中 `_verify_hash` 的正则表达式**，使其能可靠匹配 fbthrift v2026.06.22.00 的 `fetcher.py` 中 `_verify_hash` 方法的实际签名。当前正则 `(?=\n    def )` 依赖后续存在另一个 `def` 方法定义，若该方法是类/文件最后的方法则匹配失败。改用更稳健的匹配策略（如从 `def _verify_hash` 匹配到下一个顶级 `def ` 或文件末尾）。

### 方向 2（置信度: 中）
**验证预置 libaio tarball 的内部目录结构与 manifest subdir 一致**，确保 `fix_getdeps.py` 修改后的 `subdir = libaio-0.3.113` 与 tarball 解压后的实际目录名一致。

### 方向 3（置信度: 低）
**若前两个方向修复后仍然失败**，需考虑是否是构建资源不足导致超时。fbthrift + folly + fizz + mvfst + wangle 的完整构建对于普通 CI runner 可能资源消耗过高，考虑增加 CI runner 的资源配额或超时阈值。

## 需要进一步确认的点
1. **获取未截断的完整日志**：当前日志在 2MiB 处被截断，需要获取完整的 Docker build 输出，确认 `fatal: not a git repository` 之后、Jenkins 断连之前是否有任何编译错误或链接错误。
2. **确认 `fetcher.py` 的实际 `_verify_hash` 方法签名**：从 fbthrift v2026.06.22.00 上游仓库的 `build/fbcode_builder/getdeps/fetcher.py` 文件中确认 `_verify_hash` 方法的实际定义，验证 `fix_getdeps.py` 中的正则是否能正确匹配。
3. **确认 libaio tarball 内部目录结构**：解压 `libaio-libaio-0.3.113.tar.gz`，确认其顶层目录名为 `libaio-libaio-0.3.113` 还是 `libaio-0.3.113`，以判断 manifest subdir 修改是否正确。
4. **检查 CI runner 资源状态**：查询 `ecs-build-docker-x86-hk` 节点的系统日志（dmesg/OOM killer），确认是否因 OOM 导致 Docker 进程被杀死。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
若修复方向涉及 `fix_getdeps.py` 中 `_verify_hash` 的正则匹配修改，code-fixer 必须：
1. 从 fbthrift v2026.06.22.00 的上游仓库（`https://github.com/facebook/fbthrift.git`，tag `v2026.06.22.00`）获取 `build/fbcode_builder/getdeps/fetcher.py` 文件。
2. 确认 `_verify_hash` 方法的实际签名（参数名称、数量、是否有装饰器），验证新正则确实能匹配目标内容后再提交。
3. 解压 `libaio-libaio-0.3.113.tar.gz`（PR 提交的二进制文件），确认其内部顶层目录名，与 `fix_getdeps.py` 中修改后的 manifest subdir 值一致。
