# CI 失败分析报告

## 基本信息
- PR: #2983 — chore(fbthrift): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 正则patch上游源文件可能失效
- 新模式症状关键词: getdeps, fetcher.py, _verify_hash, re.sub, DOTALL, log truncated, 2MiB

## 根因分析

### 直接错误
日志在 `#11 2130.5`（Writing cargo config for fbthrift）之后被截断（2MiB 上限），紧随其后的是 Jenkins 端报错 `FATAL: command execution failed` 和 `ChannelClosedException`。Docker build 在约 35 分钟后崩溃，但**实际导致 docker build 失败的报错信息不在提供的日志中**。

```
#11 2130.5 Writing cargo config for fbthrift to /tmp/.../build/fbthrift/source/thrift/lib/rust/.cargo/config.toml
FATAL: command execution failed
java.io.EOFException
Caused: java.io.IOException: Unexpected termination of the channel
Caused: hudson.remoting.ChannelClosedException: Channel "hudson.remoting.Channel@24d4cc0d:ecs-build-docker-x86-hk": Remote call on ecs-build-docker-x86-hk failed. The channel is closing down or has closed down
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

日志中还有一个值得注意的非致命信息：
```
#11 725.2 fatal: not a git repository (or any of the parent directories): .git
```
该信息出现在 boost header 安装之后，不影响后续依赖解析（folly、fizz、mvfst、wangle 均成功 resolve pinned rev），属于 getdeps 构建系统内部的非致命 git 检测警告。

### 根因定位
- 失败位置: 未知（日志截断，build 在 "Writing cargo config" 后崩溃）
- 失败原因: 无法从日志中确定。最可疑的因素是 `fix_getdeps.py` 中用于替换 `_verify_hash` 方法的正则表达式可能在上游 fbthrift v2026.06.22.00 的 `fetcher.py` 源码中**匹配失败**（regex 未命中任何内容，`re.sub` 返回原字符串不做修改），导致后续 libaio 或其它依赖的哈希校验未被跳过、或 fetcher.py 代码结构损坏引发 Python 语法/运行时错误。

## 根因详细分析——`fix_getdeps.py` 正则替换风险

PR 新增的 `fix_getdeps.py` 第 2 步使用以下正则替换 `fetcher.py` 中的 `_verify_hash` 方法：

```python
re.sub(
    r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )',
    'def _verify_hash(self):\n        pass',
    c2,
    flags=re.DOTALL
)
```

该正则存在以下匹配失败场景：

1. **`_verify_hash` 是类中最后一个方法**：正则依赖 lookahead `(?=\n    def )` 来定位下一个方法定义的边界。若 `_verify_hash` 之后没有另一个 `def` 开头的方法（例如它是类末尾方法、或后面是空行/注释/类结束），正则完全无法匹配，`re.sub` 不做任何替换，原方法保留。

2. **方法签名包含类型注解中的 `)`**：`[^)]*` 匹配除 `)` 外的任意字符，但若上游版本的 `_verify_hash` 签名为 `def _verify_hash(self, download_path: Path, expected_hash: str) -> None:`，则参数列表中无额外 `)`，但 `[^:]*` 之后用 `:` 来定位冒号——这在大多数情况下能工作，但如果签名复杂（如参数默认值含字符串中的 `:`），仍可能出错。

3. **下一个方法的缩进不是 4 空格**：lookahead 期望 `    def `（4 空格 + `def` + 空格），若上游使用 tab 或不同缩进宽度则不匹配。

4. **下一个方法有装饰器**：若 `_verify_hash` 后紧跟一个带装饰器的方法（如 `@staticmethod\n    def ...`），`(?=\n    def )` 无法匹配到装饰器行之后的 `def`，会继续跳过整个装饰器+方法体，直到找到下一个未装饰的 `def`——这可能意外删除多个方法。

**若正则匹配失败**，`_verify_hash` 原方法保留。此时 getdeps 在安装 libaio 等依赖时会执行哈希校验。如果预置的 `libaio-libaio-0.3.113.tar.gz` 的哈希与 manifest 中的期望值不匹配（例如原作者重新打包时修改了压缩参数），构建会在该步骤失败。

**若正则匹配成功但替换范围超出预期**（如吞掉了后续方法），会导致 `fetcher.py` 语法错乱，Python import 阶段就会报 `IndentationError` / `SyntaxError`，构建立即中断。

由于日志截断，无法判断属于以上哪种情况。

### 与 PR 变更的关联
PR 新增了 `fix_getdeps.py` 脚本，该脚本是本次构建流程的**核心补丁**，出问题即直接导致构建失败。所有失败症状（构建进行到 cargo config 阶段后崩溃）与 `fix_getdeps.py` 的正则替换逻辑高度相关。

## 修复方向

### 方向 1（置信度: 中）
**放弃正则替换，改用更可靠的方式跳过 `_verify_hash`**。

不在 `fetcher.py` 中做正则替换，而是在 Dockerfile 中通过 sed 或 Python 的 AST 操作、或替换整个 fetcher.py 文件中的 `_verify_hash` 方法。或者干脆不走 `getdeps.py` 的哈希校验流程——如果有命令行参数 `--skip-hash-check` 或环境变量可以控制，直接使用它们。

更稳健的做法：在 `fix_getdeps.py` 的第一阶段（修复 openEuler 发行版识别）之后，复制一份已知可靠的、已预先写好 `pass` 版本的 `fetcher.py` 到镜像中，覆盖上游文件，完全避开正则风险。

### 方向 2（置信度: 低）
**确认正则确实能匹配上游 v2026.06.22.00 的 `fetcher.py` 后，调试非正则因素**。

若验证正则匹配无误，失败原因可能是：
- 构建超时（fbthrift 编译极其耗时，35 分钟可能不够）
- OOM（Docker build 阶段内存不足被 kill）
- libaio 预置 tarball 的哈希与 manifest 不匹配
- 其他编译依赖问题（如 boost 1.83.0 与 fbthrift 的兼容性）

## 需要进一步确认的点
1. **获取完整构建日志**：当前日志在 2MiB 处截断，丢失了 `#11 2130.5` 之后的所有 Docker build 输出。需要重新触发 CI 或从 Jenkins 获取未截断的完整日志，才能看到实际的构建错误。
2. **验证正则是否能匹配上游文件**：从 fbthrift v2026.06.22.00 的 `build/fbcode_builder/getdeps/fetcher.py` 中提取 `_verify_hash` 方法及其上下文，用 `fix_getdeps.py` 中的正则做匹配测试，确认 `re.sub` 是否真的替换了目标方法。
3. **确认 libaio tarball 哈希**：验证预置 `libaio-libaio-0.3.113.tar.gz` 的 SHA256/SHA1 是否与 fbthrift 上游 manifest 中声明的哈希一致。
4. **检查构建资源限制**：确认 Jenkins job 的 timeout 设置和内存限制是否足以完成 fbthrift 的完整编译。

## 修复验证要求
若修复方向 1 中涉及修改 `fetcher.py` 的替换逻辑：
- **code-fixer 必须从 fbthrift v2026.06.22.00 的 `build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的实际签名及上下文**，验证新的替换方式（无论用 sed、Python AST 还是预置文件覆盖）确实能达到跳过哈希校验的目的。
- 如果改用正则方案，必须先用该正则对上游实际文件做匹配测试，确认有且仅有一个匹配，且替换后文件语法正确、`import` 不报错。
- 如果更换为 sed 方案，必须验证 `_verify_hash` 方法的行号范围和内容在当前版本的上游文件中准确无误。
