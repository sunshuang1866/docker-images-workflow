# CI 失败分析报告

## 基本信息
- PR: #2983 — chore(fbthrift): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 代理通道中断
- 新模式症状关键词: ChannelClosedException, EOFException, Unexpected termination of the channel, Remote call failed, eofexception

## 根因分析

### 直接错误
```
#11 2130.5 Writing cargo config for fbthrift to /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/build/fbthrift/source/thrift/lib/rust/.cargo/config.toml
FATAL: command execution failed
java.io.EOFException
Caused: java.io.IOException: Unexpected termination of the channel
Caused: hudson.remoting.ChannelClosedException: Channel "hudson.remoting.Channel@24d4cc0d:ecs-build-docker-x86-hk": Remote call on ecs-build-docker-x86-hk failed. The channel is closing down or has closed down
```

### 根因定位
- 失败位置: 无法精确定位（日志被截断 + 代理通道中断）
- 失败原因: Docker 构建进程运行超过 35 分钟（#11 2130.5 秒），期间编译 boost、folly、fizz、mvfst、wangle 等依赖，当进入 fbthrift 自身编译阶段时，Jenkins 远端代理节点 `ecs-build-docker-x86-hk` 与主控端的通道中断（`ChannelClosedException`），导致 Jenkins 无法获取构建进程的真实退出状态，将整个 job 标记为失败。日志在 #11 525.7 处被裁剪（2MiB 限制），真实错误输出已丢失。

### 额外发现：`fix_getdeps.py` 正则存在潜在缺陷

在审查 PR diff 时发现 `fix_getdeps.py` 的第 2 项修补存在设计隐患，但无法确认是否直接导致本次失败。

**问题正则**（`fix_getdeps.py:19-24`）：
```
def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )
```

该正则依赖正向前瞻 `(?=\n    def )` 来界定 `_verify_hash` 方法体的结束边界——即假设该方法后面紧跟另一个 `def` 方法。若 `_verify_hash` 是类中最后一个方法（后面没有其他 `def`），前瞻将永远无法匹配，`re.sub` 静默返回原文件内容不做替换，`_verify_hash` 方法保持原样。这意味着预置的 libaio tarball 仍会经过哈希校验，若 hash 不匹配将导致构建失败。但本次日志中未见明确 hash mismatch 错误，且构建已通过 libaio 阶段（进入 boost 安装），故无法断定此问题为根因。

**libaio subdir 修正**（`fix_getdeps.py:26-29`）：
```
c3 = c3.replace('subdir = libaio-libaio-0.3.113', 'subdir = libaio-0.3.113')
```
上游 pagure.io 发布的 `libaio-libaio-0.3.113.tar.gz` 解压后目录名通常为 `libaio-libaio-0.3.113`（与 GitHub release 命名一致），将 manifest 中的 `subdir` 改为 `libaio-0.3.113` 可能导致 getdeps 在解压后找不到目标目录。但同样，日志中未见此阶段的报错。

### 与 PR 变更的关联
PR 新增了一个完整的 fbthrift Dockerfile 构建流程（纯新增文件），包含：
- 系统依赖安装
- `fix_getdeps.py` 对上游构建脚本的三处 patch
- 预置 libaio tarball 并绕过哈希校验
- 执行 `getdeps.py build fbthrift` 完整构建

构建失败发生在 fbthrift 编译阶段，与 PR 新增的构建流程直接相关，但具体是代码缺陷还是构建资源不足（OOM / 超时）无法从现有日志确认。

## 修复方向

### 方向 1（置信度: 低）
**修复 `fix_getdeps.py` 正则，使其在 `_verify_hash` 为类中最后一个方法时也能正确匹配。**

当前正则 `def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )` 的 `(?=\n    def )` 前瞻要求方法后必须有另一个 `def`。应改为能匹配到方法体末尾（类缩进结束位置或文件末尾）的正则，例如使用 `(?=\n    def |\n\S)` 匹配下一个 `def` 或下一个非缩进行，或直接匹配到 `self.` 所在类级别缩进结束。若无法通过正则可靠截取，可改为直接重写整个 `_verify_hash` 方法文件内容。

**⚠️ 修复验证要求**：code-fixer 必须从 fbthrift `v2026.06.22.00` 上游仓库获取 `build/fbcode_builder/getdeps/fetcher.py` 的实际文件内容，确认 `_verify_hash` 方法的实际签名和位置（是否为类中最后一个方法），验证新正则确实能匹配目标方法后再提交。

### 方向 2（置信度: 低）
**确认 libaio tarball 内部目录结构与 manifest subdir 设置一致。**

PR 将 `subdir` 从 `libaio-libaio-0.3.113` 改为 `libaio-0.3.113`，但 lbound pagure.io 发布的 `libaio-libaio-0.3.113.tar.gz` 解压后目录名通常为 `libaio-libaio-0.3.113`。code-fixer 需下载上游 tarball 并检查实际目录名，确保 `subdir` 值与其一致。

### 方向 3（置信度: 低）
**Jenkins 代理通道中断——可能因构建资源不足（OOM / 超时 / 磁盘满）。**

若修复方向 1 和 2 后构建仍失败，可能是构建节点资源不足导致。需检查 CI 节点 `ecs-build-docker-x86-hk` 的构建日志（如 dmesg OOM kill 记录）和 Jenkins job 超时配置，考虑增加构建内存/磁盘配额或延长超时时间。

## 需要进一步确认的点
1. **fbthrift v2026.06.22.00 的 `build/fbcode_builder/getdeps/fetcher.py` 中 `_verify_hash` 方法是否在类中最后**：直接决定 `fix_getdeps.py` 正则能否生效。
2. **libaio tarball (`libaio-libaio-0.3.113.tar.gz`) 解压后的实际目录名**：验证 subdir 修正是否正确。
3. **上游 fbthrift v2026.06.22.00 是否已有更优的 openEuler 支持方式**：如 getdeps 是否已原生识别 openEuler，避免自行 patch 平台识别文件。
4. **CI 构建节点资源状态**：OOM kill 记录、Docker daemon 日志、Jenkins job 超时阈值。

## 修复验证要求
若修复方向 1（修改 `fix_getdeps.py` 正则）被采纳，code-fixer 必须在提交前执行以下验证：
1. 从 `https://github.com/facebook/fbthrift/blob/v2026.06.22.00/build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的实际签名和完整方法体
2. 确认新正则能正确匹配并替换该方法
3. 确认替换后的 `pass` 实现不会导致 getdeps 在后续步骤中引用 `_verify_hash` 的返回值或副作用时报错
4. 本地或容器内重跑 `python3 /tmp/fix_getdeps.py` 后检查目标文件内容是否正确修改
