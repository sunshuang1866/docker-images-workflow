# CI 失败分析报告

## 基本信息
- PR: #2706 — 【自动升级】fbthrift容器镜像升级至2026.06.22.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 预置源码包结构不匹配
- 新模式症状关键词: No targets specified and no makefile found, libaio, getdeps, make, tarball

## 根因分析

### 直接错误
```
#11 334.3 Assessing libaio...
#11 334.3 Extract /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/extracted/libaio-libaio-libaio-0.3.113.tar.gz
#11 334.3 Building libaio...
#11 334.3 make: *** No targets specified and no makefile found.  Stop.
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads &&     cp /tmp/libaio.tar.gz /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.22.00/24.03-lts-sp3/Dockerfile`:18-23（`RUN` 步骤执行 `getdeps.py build fbthrift`）
- 失败原因: getdeps 在构建 libaio 依赖时，进入提取后的源码目录执行 `make`，但该目录内无 Makefile，导致 libaio 构建失败，进而整个 fbthrift 构建流程以 exit code 1 终止。

### 次要问题
日志在 #11 334.0 处出现 `!! Failed` 和多个 Boost CMake `SEND_ERROR` 消息，表明系统安装的 `boost-devel` 包与 getdeps 从源码构建的 Boost 之间存在 CMake 目标导入冲突：
```
#11 334.3 message(SEND_ERROR "Target Boost::atomic already has an imported location '${__boost_imploc}', which is being overwritten with '${_BOOST_LIBDIR}/libboost_atomic.a'")
#11 334.3 message(SEND_ERROR "Target Boost::test_exec_monitor already has an imported location...")
#11 334.3 message(SEND_ERROR "Target Boost::unit_test_framework already has an imported location...")
#11 334.3 message(SEND_ERROR "Target Boost::chrono already has an imported location...")
```
该问题源于 `--allow-system-packages` 同时启用了系统 Boost 包和 getdeps 源码构建的 Boost，但 `SEND_ERROR` 不会立即终止 cmake 处理（与 `FATAL_ERROR` 不同），后续依赖（gflags、glog、googletest）仍构建成功，说明该问题未直接导致整体失败；libaio 的 `make` 失败才是 exit code 1 的直接原因。

### 与 PR 变更的关联
PR 新增了以下文件，所有这些文件都对构建失败负有直接责任：

1. **`libaio-libaio-0.3.113.tar.gz`（二进制 tarball）**：作为预下载的 libaio 源码包，在 Dockerfile 中被 `COPY` 并 `cp` 到 getdeps 期望的下载目录位置。该 tarball 提取后缺少 Makefile，是构建失败的直接原因。可能的原因包括：
   - tarball 是从错误的 URL 获取的（如 Ubuntu Launchpad 的 Debian 打包源码 vs 上游 libaio 发布源码，二者目录结构不同）
   - tarball 下载不完整或被损坏
   - tarball 内部目录结构与 getdeps 清单（manifest）中 libaio 构建路径不匹配

2. **`fix_getdeps.py`**：该脚本通过正则 patch `fetcher.py` 的 `_verify_hash` 方法来绕过 libaio tarball 的哈希校验。即使绕过哈希校验成功，也无法解决 tarball 内容本身不完整或结构不匹配的问题。另外，如果该正则未能匹配目标方法签名（fbthrift v2026.06.22.00 的新版本 fetcher.py 可能有不同的 `_verify_hash` 实现），则连绕过哈希校验都做不到，但该情况会导致不同的错误（哈希校验失败），而非当前看到的 `make: no makefile found`。

3. **`Dockerfile`**：新增的构建步骤组合了上述两个文件，整体构建流程依赖预下载的 libaio tarball 能通过 getdeps 正常构建，但实际不能。

## 修复方向

### 方向 1（置信度: 中）
验证并重新获取 libaio 源码 tarball。从 libaio 官方发布源（如 `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 或 fbthrift getdeps manifest 中定义的 libaio 下载 URL）重新下载对应版本的源码 tarball，确保其内部包含 Makefile 和完整的构建系统，替换当前 PR 中提供的二进制 tarball。

### 方向 2（置信度: 低）
如果方向 1 无效，检查 fbthrift v2026.06.22.00 的 getdeps manifest 中 libaio 的构建方式是否已变更。上游可能已改用 cmake、meson 或其他构建系统，导致 getdeps 的 make 命令不再适用。此时需要：
- 根据 manifest 中的实际构建方式，提供对应结构的 tarball
- 或调整 `fix_getdeps.py` 中的 patch 逻辑以适配新的构建系统

### 方向 3（置信度: 低）
解决 Boost CMake 冲突问题。如果仅修复 libaio 后 Boost 冲突仍导致退出，可考虑在 `dnf install` 中移除 `boost-devel` 依赖，让 getdeps 完全从源码构建 Boost，避免目标冲突。但此方向优先级较低，因为日志显示 Boost 的 `SEND_ERROR` 未直接导致退出。

## 需要进一步确认的点

1. **libaio tarball 内容验证**：需要下载当前 PR 中提供的 `libaio-libaio-0.3.113.tar.gz` 二进制文件，解压后检查：
   - 顶层目录名称是否为 `libaio-libaio-0.3.113`
   - 顶层目录内是否包含 `Makefile`
   - 该 tarball 是从哪个 URL 获取的（与 fbthrift manifest 中定义的 URL 对比）
2. **fix_getdeps.py 正则有效性验证**：需要从 `fbthrift v2026.06.22.00` 的 `build/fbcode_builder/getdeps/fetcher.py` 中获取 `_verify_hash` 方法的实际签名，验证 `fix_getdeps.py` 中的正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 是否能够匹配。
3. **fbthrift v2026.06.22.00 与 v2026.05.18.00 的 getdeps manifest 差异**：对比两个版本的 libaio 构建清单，确认上游是否变更了 libaio 的构建方式或下载 URL。

## 修复验证要求

**（fix_getdeps.py 正则验证）**：code-fixer 在提交前，必须从 fbthrift v2026.06.22.00 的 `build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的实际签名，验证 `fix_getdeps.py` 第 17-20 行中的正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 确实能匹配目标方法，并将源码文件替换为新内容。

**（libaio tarball 验证）**：code-fixer 必须确认重新获取的 libaio tarball 解压后在顶层目录（或 getdeps manifest 指定的构建目录）中确实存在 Makefile，且 `make` 命令能不报错地构建 libaio。
