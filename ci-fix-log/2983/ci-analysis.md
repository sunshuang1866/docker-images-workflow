# CI 失败分析报告

## 基本信息
- PR: #2983 — chore(fbthrift): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: Jenkins Agent 通道中断
- 新模式症状关键词: ChannelClosedException, EOFException, Unexpected termination of the channel, ecs-build-docker-x86-hk

## 根因分析

### 直接错误
```
FATAL: command execution failed
java.io.EOFException
Caused: java.io.IOException: Unexpected termination of the channel
Caused: hudson.remoting.ChannelClosedException: Channel "hudson.remoting.Channel@24d4cc0d:ecs-build-docker-x86-hk": Remote call on ecs-build-docker-x86-hk failed. The channel is closing down or has closed down
FATAL: Unable to delete script file /tmp/jenkins3161304096436833533.sh
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: Jenkins 构建节点 `ecs-build-docker-x86-hk`（x86_64架构），发生在 `#11`（Docker build 步骤）执行期间
- 失败原因: Jenkins Master 与构建节点 `ecs-build-docker-x86-hk` 之间的 remoting 通道意外中断（`ChannelClosedException`），导致正在执行中的 Docker build 被强制终止。Docker build 当时已运行约 2130 秒（35 分钟），正处于 fbthrift 及其依赖（boost、folly、fizz、mvfst、wangle）的编译阶段，日志输出量已触发 2MiB 截断限制。

### 与 PR 变更的关联
**无法确定是否存在直接关联**。PR 新增了 fbthrift v2026.06.22.00 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和配套修补脚本 `fix_getdeps.py`。Docker build 在 Jenkins Agent 崩溃前已顺利通过以下阶段：
1. dnf 安装系统依赖（无报错）
2. git clone fbthrift 源码（无报错）
3. 执行 `fix_getdeps.py` 修补脚本（无报错）
4. getdeps 成功解析并开始安装依赖：boost（525秒起）、folly（901秒）、fizz（1390秒）、mvfst（1606秒）、wangle（2017秒）、fbthrift cargo config（2130秒）

日志中唯一的非致命警告是 `#11 725.2 fatal: not a git repository (or any of the parent directories): .git`，该警告出现在 boost header 安装完毕之后、folly 依赖解析之前，系 getdeps 在构建某依赖的提取 tarball 目录中执行 git 命令所致，不影响构建流程。

由于 Jenkins Agent 通道在 Docker build 完成前中断，**无法判断 Docker build 本身是否会最终成功**。

## 修复方向

### 方向 1（置信度: 低）
**重试构建**。该失败为 Jenkins 基础设施层面的通道中断（可能由网络波动、Agent 资源耗尽或 Jenkins 超时引起），与 PR 代码改动无直接关联。重新触发 CI 流水线有较大概率通过。

### 方向 2（置信度: 低）
**检查 `fix_getdeps.py` 中 `_verify_hash` 正则表达式的匹配正确性**。该脚本第 17-22 行使用正则 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` 替换 `fetcher.py` 中的 `_verify_hash` 方法为空实现。存在以下风险：
- 如果 `_verify_hash` 是该类的最后一个方法，则 `(?=\n    def )` 前瞻断言无法匹配，正则整体匹配失败，`re.sub` 返回原字符串不变，哈希校验代码未被替换；
- 如果 `_verify_hash` 方法体内部包含嵌套的 `def` 语句，懒匹配 `.*?` 可能过早终止，导致替换不完整。

由于 Docker build 在到达 libaio 哈希校验步骤之前即被中断，无法从日志确认该正则是否生效。

## 需要进一步确认的点
1. **重试 CI 构建**：确认 Docker build 是否能完整通过，排除本次失败为偶发性基础设施问题。
2. **验证 `fix_getdeps.py` 正则**：从 fbthrift v2026.06.22.00 上游仓库获取 `build/fbcode_builder/getdeps/fetcher.py` 文件，检查 `_verify_hash` 方法的实际签名和位置（是否为类中最后一个方法），确认正则 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` 能够正确匹配并替换整个方法体。
3. **检查 Jenkins 节点资源**：确认 `ecs-build-docker-x86-hk` 节点的磁盘空间和内存是否充足，fbthrift 完整构建（含 boost、folly、fizz、mvfst、wangle 等重型 C++ 依赖）对资源消耗较大。
4. **检查上游 fbthrift v2026.06.22.00 的 `build/fbcode_builder/getdeps/getdeps_platform.py`**：确认 `openeuler` 字符串添加到发行版元组后，getdeps 能正确识别 openEuler 系统并安装对应依赖。

## 修复验证要求
若修复方向 2 被采纳（修改 `fix_getdeps.py` 中的正则），code-fixer 必须：
1. 从 fbthrift v2026.06.22.00 上游仓库获取 `build/fbcode_builder/getdeps/fetcher.py` 文件（可通过 `git clone -b v2026.06.22.00 --depth 1 https://github.com/facebook/fbthrift.git` 获取）
2. 在该文件中定位 `_verify_hash` 方法的完整签名和位置（确认参数列表、方法体结构、是否为最后一个方法）
3. 用实际文件内容验证修改后的正则表达式能否正确匹配 `_verify_hash` 方法并完整替换
4. 同样验证 `fix_getdeps.py` 中对 `getdeps_platform.py` 发行版列表的字符串替换和 `libaio` manifest 的 `subdir` 替换是否与原文件内容匹配
