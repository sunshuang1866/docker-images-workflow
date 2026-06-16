# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: libaio构建阶段失败
- 新模式症状关键词: Assessing libaio, exit code: 1, getdeps.py, libaio, fbthrift

## 根因分析

### 直接错误
```
#11 332.5 Building googletest...
#11 332.5 Assessing libaio...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build && ... && ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
------
Dockerfile:18
--------------------
  18 | >>> RUN git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build && \
  19 | >>>     cd /build && \
  ...
  23 | >>>     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift
--------------------
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile:18`（RUN 命令）
- 失败原因: `getdeps.py build fbthrift` 在执行到 libaio 依赖的评估/构建阶段时失败（exit code 1），但日志被截断，libaio 构建的具体错误信息未出现在提供的日志中。

### 日志信息分析
日志显示 getdeps 构建链路中以下依赖均已**成功构建**：
- ninja、benchmark、zlib、zstd、fmt、boost、fast_float、gflags、glog、googletest

失败点出现在 `Assessing libaio...` 之后，此后无任何 cmake 配置输出或编译错误信息，直接跳至 Docker build 整体失败。说明 libaio 的评估/构建阶段发生了错误，但真正的错误行被截断。

### 与 PR 变更的关联

**直接关联**。本次 PR 新增了 3 个文件：
1. `Dockerfile` — 包含完整的 fbthrift 构建流程
2. `fix_getdeps.py` — 两个关键 patch：① 将 "openeuler" 加入 getdeps 的发行版识别列表；② 将 `_verify_hash` 方法替换为空操作以跳过 libaio 哈希校验
3. `libaio-libaio-0.3.113.tar.gz` — 自定义 libaio 源码包（二进制文件）

失败发生在 `fix_getdeps.py` 执行后、getdeps 处理 libaio 依赖的阶段。可能的原因包括：
- **libaio 源码编译失败**：自定义 tarball 中的 libaio 源码在 openEuler 24.03-lts-sp3 + GCC 12.3.1 环境下编译出错（可能是缺少编译依赖、架构不兼容、或源码本身有问题）
- **`_verify_hash` 补丁失效**：`fix_getdeps.py` 中的正则表达式替换可能未能匹配 fbthrift v2026.06.15.00 版本 `fetcher.py` 中的实际代码结构，导致哈希校验未被跳过，自定义 tarball 因哈希不匹配而被拒绝
- **getdeps manifest 文件名不匹配**：cp 目标文件名为 `libaio-libaio-libaio-0.3.113.tar.gz`，若 fbthrift 新版本的 manifest 中 libaio 对应的文件名格式有变化，getdeps 可能无法识别该文件而重新下载或报错

## 修复方向

### 方向 1（置信度: 低）
检查 `fix_getdeps.py` 中的 `_verify_hash` 正则替换是否与 fbthrift v2026.06.15.00 版本的 `build/fbcode_builder/getdeps/fetcher.py` 实际代码结构匹配。在上游代码更新后，`_verify_hash` 方法的缩进或上下文可能发生变化，导致正则无法命中。需要对照目标版本的实际源码验证补丁的正确性。

### 方向 2（置信度: 低）
libaio 源码包（`libaio-libaio-0.3.113.tar.gz`）在 openEuler 24.03-lts-sp3 上编译可能需要额外的构建依赖（如 `libaio-devel` 本身或其它工具链包）。检查 libaio 的 cmake/configure 输出以确认是否因缺少依赖而导致配置失败。

### 方向 3（置信度: 低）
fbthrift v2026.06.15.00 的 getdeps manifest 可能变更了 libaio 依赖的定义（如 URL、文件名格式、版本要求等），导致自定义 tarball 的文件名 `libaio-libaio-libaio-0.3.113.tar.gz` 不再匹配新版本 manifest 的预期。需要对比新旧版本的 manifest 差异。

## 需要进一步确认的点
- **关键缺失信息**：需要获取完整的 Docker 构建日志（特别是 `Assessing libaio...` 之后的部分），包含 libaio 的 cmake 配置输出、编译错误或哈希校验错误信息。当前日志在关键错误处被截断，无法确定具体失败原因。
- 确认 fbthrift v2026.06.15.00 中 `fetcher.py` 的 `_verify_hash` 方法实际代码结构，验证 `fix_getdeps.py` 正则替换是否能正确命中。
- 确认 fbthrift v2026.06.15.00 的 getdeps manifest 中 libaio 依赖的定义是否与之前版本一致。
- 确认 `libaio-libaio-0.3.113.tar.gz` 源码包内容完整性及其在目标平台上的可编译性。
