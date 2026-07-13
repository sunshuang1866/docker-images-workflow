# CI 失败分析报告

## 基本信息
- PR: #2983 — chore(fbthrift): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Jenkins 通道断连
- 新模式症状关键词: java.io.EOFException, ChannelClosedException, Unexpected termination of the channel, Remote call failed

## 根因分析

### 直接错误
```
FATAL: command execution failed
java.io.EOFException
Caused: java.io.IOException: Unexpected termination of the channel
Caused: hudson.remoting.ChannelClosedException: Channel "hudson.remoting.Channel@24d4cc0d:ecs-build-docker-x86-hk": Remote call on ecs-build-docker-x86-hk failed. The channel is closing down or has closed down
```
```
FATAL: Unable to delete script file /tmp/jenkins3161304096436833533.sh
java.io.EOFException
Caused: hudson.remoting.ChannelClosedException: Channel "hudson.remoting.Channel@24d4cc0d:ecs-build-docker-x86-hk": Remote call on ecs-build-docker-x86-hk failed. The channel is closing down or has closed down
```

### 根因定位
- 失败位置: Jenkins 远程代理节点 `ecs-build-docker-x86-hk`，Shell 执行步骤
- 失败原因: Docker 构建（`getdeps.py build fbthrift`）运行超过 35 分钟后，Jenkins master 与远程构建节点 `ecs-build-docker-x86-hk` 之间的 remoting 通道意外断开（`java.io.EOFException` → `ChannelClosedException`），导致 shell step 被标记为失败。Docker 构建自身在断连前进展正常（已完成 boost 安装、folly/fizz/mvfst/wangle 依赖解析，正在生成 fbthrift Rust cargo 配置），无编译错误输出。

### 与 PR 变更的关联
本次 PR 新增了一个完整的 fbthrift 源码编译 Dockerfile，通过 `getdeps.py` 构建 fbthrift 及其全部依赖（boost、folly、fizz、mvfst、wangle），构建过程耗时极长（日志记录到 35.5 分钟时仍在进行中）。长时间构建可能触发 Jenkins 代理节点的资源限制（OOM、超时等），导致代理进程崩溃/失联。此外，`fix_getdeps.py` 中用于跳过 libaio 哈希校验的正则表达式存在健壮性隐患（见下文），重试时可能暴露该问题。

## 修复方向

### 方向 1（置信度: 中）
本次失败的直接原因是 Jenkins 代理通道断连，属于基础设施问题。建议直接**重试 CI**，观察是否稳定复现。如果重试后成功，则无需修改代码。

### 方向 2（置信度: 低）
如果重试仍然失败，需排查 `fix_getdeps.py` 中跳过 `_verify_hash` 的正则表达式是否在目标版 fbthrift 的 `fetcher.py` 中成功匹配。当前正则 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` 依赖以下假设：
- 方法签名中无嵌套括号
- 下一个 `def` 关键字恰好缩进 4 个空格
- `_verify_hash` 不是类中最后一个方法

若正则未匹配（静默失败），则 libaio 哈希校验未被跳过，getdeps 可能因哈希不匹配而失败。

### 方向 3（置信度: 低）
若 Docker 构建因资源不足（内存/OOM）被 kill，可考虑在 Dockerfile 中为 `getdeps.py` 添加 `--num-jobs` 参数限制并行编译数（如 `--num-jobs 2`），减少峰值内存消耗。

## 需要进一步确认的点
1. Jenkins 节点 `ecs-build-docker-x86-hk` 的**资源使用情况**：需要确认该节点在构建期间是否发生 OOM kill 或磁盘满等事件
2. 目标版 fbthrift（`v2026.06.22.00`）中 `build/fbcode_builder/getdeps/fetcher.py` 的 **`_verify_hash` 方法实际签名和位置**：需确认 `fix_getdeps.py` 中的正则是否能命中
3. `libaio-libaio-0.3.113.tar.gz` 二进制文件（PR 中新增）的**实际内部目录结构**：确认 `subdir` 修复 `libaio-libaio-0.3.113` → `libaio-0.3.113` 是否正确

## 修复验证要求
若修复方向涉及修改 `fix_getdeps.py` 中的正则表达式，code-fixer 必须在提交前：
- 从 `https://github.com/facebook/fbthrift.git` 的 `v2026.06.22.00` tag 获取 `build/fbcode_builder/getdeps/fetcher.py` 的实际内容
- 验证 `_verify_hash` 方法的完整签名（包括类型注解）和前后代码上下文
- 用修改后的正则对该文件运行 `re.sub`，确认替换成功
- 同时验证 `build/fbcode_builder/manifests/libaio` 中 `subdir` 字段的实际值
