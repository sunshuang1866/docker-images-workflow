# CI 失败分析报告

## 基本信息
- PR: #2804 — 【自动升级】fbthrift容器镜像升级至2026.06.29.00版本.
- 失败类型: build-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: fbthrift上游编译失败
- 新模式症状关键词: ninja: build stopped, cannot make progress due to previous errors, fbthrift, folly, Expected.h

## 根因分析

### 直接错误
```
#11 3094.5 ninja: build stopped: cannot make progress due to previous errors.
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 ... && python3 /tmp/fix_getdeps.py && ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

日志显示构建进程到约 [876/895]（约 98% 进度）后，ninja 因先前的编译错误中止。日志中可见大量 `-Wstringop-overread` 警告（涉及 folly 的 `Constexpr.h:56` 和 `Pretty.h:136`，由 fbthrift 的 `JSONProtocolCommon-inl.h:672` 处 `castIntegral` 模板实例化触发），但**实际导致 ninja 停止的编译错误信息在日志中被截断，未能在提供的日志中找到明确的 `error:` 行**。

### 根因定位
- 失败位置: Dockerfile:18（`RUN git clone ... && ./build/fbcode_builder/getdeps.py ... build fbthrift` 步骤中的 ninja 编译阶段）
- 失败原因: fbthrift v2026.06.29.00 的 C++ 源码在 ninja 编译过程中存在编译错误，但具体错误行因日志截断无法确定。从上下文看，错误与 folly 模板的实例化链路强相关（涉及 `folly::Expected`、`folly::Range`、`folly::constexpr_strlen` 等），疑似新版本 fbthrift 代码与系统预装的 folly 版本存在 API 兼容性问题。

### 与 PR 变更的关联
PR 新增了 fbthrift v2026.06.29.00 的 Dockerfile 及配套 `fix_getdeps.py` 补丁脚本。构建失败发生在此新版本 Dockerfile 的编译阶段，因此**与 PR 变更直接相关**（新版本源码的构建问题）。依赖项（folly、fizz、mvfst、wangle）均构建成功，问题出现在 fbthrift 自身的编译阶段。

`fix_getdeps.py` 中的三项修改（openEuler 发行版识别、跳过 libaio 哈希校验、修复 libaio manifest subdir）均已成功执行（构建进展至 876/895），这些补丁本身工作正常。

## 修复方向

### 方向 1（置信度: 低）
新版本 fbthrift 的源代码与当前系统预装的 folly 版本存在 API 不兼容。需获取完整的编译错误日志（特别是 ninja 中止前的实际 `error:` 行），确认具体不兼容的函数/类型，然后根据错误类型选择：
- 降级 fbthrift 版本至可构建的版本
- 或在 Dockerfile 中为 getdeps 指定兼容的 folly commit hash
- 或在 `fix_getdeps.py` 中增加源码级 patch 修复不兼容处

### 方向 2（置信度: 低）
`fix_getdeps.py` 中用于跳过 `_verify_hash` 的正则表达式 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` 在新版本 fetcher.py 中匹配失败（方法签名变化），导致 libaio 哈希校验未正确跳过，进而导致 libaio 下载后的校验步骤失败，阻塞整个 fbthrift 构建。但从构建进度看（已达到 876/895），此可能性较低。

## 需要进一步确认的点
1. **最关键**：需要获取完整的 ninja 构建日志，特别是 `ninja: build stopped` 之前未被截断的编译错误行（应在日志中包含 `error:` 关键字的行，而非仅 `warning:`）。
2. fbthrift v2026.06.29.00 在 upstream GitHub 仓库中该 tag 的构建是否正常（可尝试在本地按 Dockerfile 方式构建验证）。
3. 系统预装 folly 的具体版本（日志中可见 commit `586774b5c30985ad5b39a578f527ab7d8637e4c8`）与 fbthrift v2026.06.29.00 的兼容性。
4. `fix_getdeps.py` 中 `_verify_hash` 正则替换在新的 fetcher.py 中是否确实命中（可在 Dockerfile 中添加 `echo` 调试确认）。

## 修复验证要求
若修复方向涉及修改 `fix_getdeps.py` 中的正则表达式（如修改 `_verify_hash` 的匹配模式或增加对 fbthrift 源码的 patch），code-fixer 必须先：
1. 从 fbthrift v2026.06.29.00 的 `build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的实际签名和实现，验证新正则确实能匹配目标内容。
2. 获取完整编译错误日志，确认失败的直接 `error:` 行，再针对性地编写修复，避免盲目修改。
