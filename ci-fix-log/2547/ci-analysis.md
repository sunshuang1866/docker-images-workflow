# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 日志截断致证据不足
- 新模式症状关键词: 日志截断, 未见致命报错, fbthrift, getdeps, boost SEND_ERROR

## 根因分析

### 直接错误
（CI 日志在依赖构建阶段被截断，未捕获到实际错误信息）

日志末端停留在 googletest 编译安装阶段（时间戳 354.0s）:
```
#11 354.0 -- Installing: /usr/local/googletest-4jQjSxQTd-HjwRWNCS8vl2kq9IImdZqr5MUHruTRYJs/include/gmock/gmock-more-matchers.h
#11 354.0 -- Installing: /usr/local/googletest-4jQjSxQTd-HjwRWNCS8vl2kq9IImdZqr5MUHruTRYJs/include/gmock/gmock.h
```
日志到此截断，其后内容未知。

### 根因定位
- 失败位置: 无法定位 — 日志截断前未出现致命错误
- 失败原因: **证据不足，无法确定根因**。日志仅覆盖了 getdeps 依赖构建阶段（zstd → boost → glog → gflags → googletest），尚未进入 fbthrift 本身的编译。实际错误极可能发生在日志截断之后的阶段。

### 与 PR 变更的关联
PR 新增了 3 个文件（Dockerfile、fix_getdeps.py、libaio tarball），与 CI 构建过程直接相关。日志中可见的构建行为与 Dockerfile 描述一致：

1. `dnf install` 安装依赖 → 日志 #8 行显示包安装正常
2. `git clone fbthrift` → 未见报错
3. `python3 fix_getdeps.py` → 未见执行输出（可能成功静默完成）
4. `./build/fbcode_builder/getdeps.py ... build fbthrift` → 日志 #11 行显示依赖构建流程（zstd、boost、glog、gflags、googletest 等）正常推进

从日志中可观察到的潜在风险点：
- **fix_getdeps.py 的 `_verify_hash` 替换正则可能匹配失败**：正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 依赖 `_verify_hash` 之后存在另一个缩进为 4 空格的方法。若 `_verify_hash` 是类中最后一个方法，正则无法匹配，libaio 哈希校验不会被跳过，后续可能因 tarball 校验失败而中止。
- **Boost 构建中大量 `SEND_ERROR` 警告**：日志 #11 176~296 行出现约 30+ 条 `Target Boost::XXX already has an imported location ... which is being overwritten` 消息。这些来自 Boost.Build 系统，虽未中断当前构建，但可能预示 cmake 配置冲突，后续 fbthrift cmake 阶段可能因此出现链接或路径问题。

## 修复方向

### 方向 1（置信度: 中）
**fix_getdeps.py 的 `_verify_hash` 正则匹配失败，libaio tarball 校验不通过。**
`_verify_hash` 方法若为类中最后方法，正则 `(?=\n    def )` lookahead 无后续 `def` 可供匹配，替换静默失败。可改用锚定方法末尾（如匹配方法体到类结束或文件结束）的更健壮替换策略，或直接在 Dockerfile 中用 sed 注释掉 hash 校验调用。

### 方向 2（置信度: 低）
**Boost 多版本/多路径冲突导致 fbthrift 链接阶段失败。**
日志中大量 `SEND_ERROR` 提示 Boost 各子库的 import location 被覆写，可能存在系统 dnf 安装的 boost-devel（`dnf install boost-devel`）与 getdeps 自建的 Boost 1.83.0 之间的符号冲突。关注 cmake 配置或链接阶段是否出现 `multiple definition`、`undefined reference` 或 `already defined` 类错误。

### 方向 3（置信度: 低）
**基础镜像或网络问题导致后续依赖下载失败。**
日志截断后可能发生 gflags/googletest 之后的其他依赖（如 double-conversion、snappy、libsodium、libevent 的 getdeps 自建版本）下载超时或 404。需获取完整日志以确认。

## 需要进一步确认的点
1. **获取完整 CI 日志**：当前日志被截断于 googletest 安装阶段（~354s），实际构建失败的错误信息完全缺失，无法进行有效诊断。
2. **确认 fbthrift fetcher.py 中 `_verify_hash` 方法的实际代码上下文**：验证正则是否能够匹配（该方法后是否存在其他方法，缩进是否恰好为 4 空格）。
3. **确认 libaio 的 CMakeLists/Manifest 中指定的 SHA256 与提供的 tarball 是否一致**：即使 `_verify_hash` 跳过成功，getdeps 可能在下载前通过 Manifest 校验 hash，需确认 Manifest 文件是否也需要 patch。
4. **检查 fbthrift v2026.06.08.00 版本是否有新增依赖**：新版本可能引入旧版本不需要的库（如 liburing-devel、libunwind-devel 等），需对照上游 changelog 检查 Dockerfile 中 `dnf install` 是否遗漏了新依赖。
