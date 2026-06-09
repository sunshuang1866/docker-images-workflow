# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: getdeps依赖构建失败
- 新模式症状关键词: getdeps, libaio, exit code: 1, fix_getdeps.py, _verify_hash, fetcher.py

## 根因分析

### 直接错误
```
#11 336.7 Assessing libaio...
#11 336.7 Download with file:///tmp/libaio.tar.gz -> .../libaio-libaio.tar.gz ...
#11 336.7 .. 8192 of 89590  [Complete in 0.004532 seconds]
#11 336.7 Content-type: application/x-tar
#11 336.7 Content-length: 89590
#11 336.7 Last-modified: Tue, 09 Jun 2026 19:39:13 GMT
#11 336.7
#11 336.7
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} ... && ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
------
Dockerfile:18
```

日志在 libaio 下载完成后立即报错退出，但**截断点之后的具体错误信息缺失**——getdeps 在 libaio 下载后的下一步（哈希校验/解压/构建 libaio，或构建 fbthrift 自身）失败，但具体报错行未被捕获到日志中。

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/Dockerfile`:18（`getdeps.py build fbthrift` 命令）
- 失败原因: `getdeps.py` 构建 fbthrift 及其依赖 libaio 的过程中失败，日志截断导致具体错误不可见。最可能的原因是 (1) `fix_getdeps.py` 中的 `_verify_hash` 正则替换未生效，导致 getdeps 对自定义 libaio tarball 做哈希校验失败；或 (2) libaio / fbthrift 编译阶段缺少某个构建依赖或存在编译错误。

### 与 PR 变更的关联
PR 新增了整个 fbthrift 2026.06.08.00 版本的 Dockerfile、`fix_getdeps.py` 补丁脚本和 libaio 二进制 tarball。失败直接由这些新增文件中的 `getdeps.py build fbthrift` 命令触发。前置依赖（glog、googletest、gflags 等）均构建成功，失败发生在 libaio 或其后续步骤。

## 修复方向

### 方向 1（置信度: 中）
`fix_getdeps.py` 中对 `fetcher.py` 的 `_verify_hash` 方法的正则替换可能未正确匹配上游代码。getdeps 在 libaio 下载完成后执行哈希校验，因自定义 tarball 哈希与 manifest 中预期值不匹配而失败。

验证方法：检查 `getdeps.py build fbthrift` 的完整输出，搜索 "hash" 或 "checksum" 相关报错。若确认是哈希校验失败，需调整 `fix_getdeps.py` 中 `re.sub` 的正则表达式，确保能匹配当前版本 fbthrift 的 `build/fbcode_builder/getdeps/fetcher.py` 中的 `_verify_hash` 方法签名和缩进风格。

### 方向 2（置信度: 低）
libaio 编译阶段缺少必要的构建依赖（如 autoconf、automake 等），或 libaio 源码与 openEuler 24.03-lts-sp3 上的工具链不兼容。

验证方法：获取 getdeps 完整输出日志，查看 libaio 的 cmake/configure 阶段是否有 "Could NOT find" 或 "configure: error" 类报错。若确认，需在 Dockerfile 的 `dnf install` 中补充对应的 `-devel` 包。

### 方向 3（置信度: 低）
libaio tarball 内容不正确（如目录结构、版本命名与 getdeps manifest 预期不符），导致解压后无法找到构建入口文件。

验证方法：获取完整日志，检查是否有 "No such file or directory" 类错误。若确认，需检查 `libaio-libaio-0.3.113.tar.gz` 的内部目录结构是否与 getdeps 的 libaio manifest 中 `url`/`build` 配置匹配。

## 需要进一步确认的点
1. **获取 getdeps 完整输出**：当前日志在 libaio 下载 "Complete" 后被截断，无法看到后续的哈希校验、解压、编译等步骤的输出。需要从 Docker build 的完整输出中提取 `#11` 步骤在 `Assessing libaio...` 之后的所有日志行，定位第一条 `ERROR` 或 `FATAL` 信息。
2. **验证 `fix_getdeps.py` 正则是否生效**：在构建环境中单独运行 `fix_getdeps.py` 后，检查 `fetcher.py` 中 `_verify_hash` 是否已被替换为 `pass` 实现。可用 `grep -A3 "def _verify_hash" build/fbcode_builder/getdeps/fetcher.py` 验证。
3. **确认 libaio tarball 内部结构**：检查 `libaio-libaio-0.3.113.tar.gz` 的顶层目录结构和文件布局，与历史成功版本（如 2026.05.18.00）的 libaio 构建方式对比是否有变化。
4. **检查 fbthrift v2026.06.08.00 上游 manifest 变更**：比对 fbthrift 的 `build/fbcode_builder/manifests/libaio` 和 `build/fbcode_builder/manifests/fbthrift` 两个 manifest 文件在上个成功版本 (v2026.05.18.00) 到当前版本 (v2026.06.08.00) 之间是否有变动，特别是 libaio 的版本号、下载 URL 模板、或构建命令的变化。
