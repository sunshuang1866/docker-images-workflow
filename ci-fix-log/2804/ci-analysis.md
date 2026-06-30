# CI 失败分析报告

## 基本信息
- PR: #2804 — 【自动升级】fbthrift容器镜像升级至2026.06.29.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 预置tarball源文件缺失
- 新模式症状关键词: `make: *** No targets specified and no makefile found`, `libaio`, `tarball`, `getdeps`, `Extract`

## 根因分析

### 直接错误
```
#11 339.0 Extract /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/extracted/libaio-libaio-libaio-0.3.113.tar.gz
#11 339.0 Building libaio...
#11 339.0 cd /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/extracted/libaio-libaio-libaio-0.3.113.tar.gz/libaio-0.3.113 && make -j8 ENABLE_SHARED=0 PREFIX=/usr/local/libaio-0VuhphKVHSCSjWfeMZYLWX5vFSwc7QCEzrEw0mT-b4Y prefix=/usr/local/libaio-0VuhphKVHSCSjWfeMZYLWX5vFSwc7QCEzrEw0mT-b4Y
#11 339.0 make: *** No targets specified and no makefile found.  Stop.
```

以及次级 cmake 报错（可能有叠加影响）：
```
#11 339.0 message(SEND_ERROR "Target Boost::atomic already has an imported location '${__boost_imploc}', which is being overwritten with '${_BOOST_LIBDIR}/libboost_atomic.a'")
#11 339.0 message(SEND_ERROR "Target Boost::test_exec_monitor already has an imported location...")
#11 339.0 message(SEND_ERROR "Target Boost::unit_test_framework already has an imported location...")
#11 339.0 message(SEND_ERROR "Target Boost::chrono already has an imported location...")
#11 338.7 !! Failed
```

### 根因定位
- 失败位置: Dockerfile:18（`RUN` 步骤，getdeps 构建 libaio 阶段）
- 失败原因: 预置的 libaio tarball（`libaio-libaio-0.3.113.tar.gz`）解压到 `libaio-0.3.113/` 子目录后，该目录内缺少 Makefile，`make` 命令无法执行。tarball 内容不完整或获取来源不正确，未能包含 libaio 的完整构建文件。

### 与 PR 变更的关联
**强关联**。本次 PR 新增的全部 3 个核心文件均直接涉及失败构建流程：

1. **Dockerfile**: 第 21 行 `cp /tmp/libaio.tar.gz ...libaio-libaio-libaio-0.3.113.tar.gz` 将提交的 tarball 复制到 getdeps 下载缓存目录，作为 libaio 的"预下载"源文件。此 tarball 内容不完整，导致解压后无 Makefile。
2. **fix_getdeps.py 第 3 步**（第 23-27 行）: 将 libaio manifest 的 `subdir` 从 `libaio-libaio-0.3.113` 修改为 `libaio-0.3.113`，与 tarball 内部目录结构匹配。`subdir` 路径导航正确（日志中 `cd` 命令成功进入 `libaio-0.3.113/`），但该目录内容缺失。
3. **libaio-libaio-0.3.113.tar.gz**（二进制文件）: 作为预置源代码包提交，但其实际内容缺少构建必需文件（Makefile 等），导致 `make` 执行失败。

此外，日志中 Boost cmake `SEND_ERROR` 提示 `dnf` 安装的 `boost-devel` 与 getdeps 自建 boost 的 cmake imported targets 存在冲突，可能构成次级失败叠加因素。

## 修复方向

### 方向 1（置信度: 中）
重新获取正确的 libaio 0.3.113 源码 tarball。从 libaio 官方仓库（https://pagure.io/libaio）的 `libaio-0.3.113` tag 生成或下载完整归档，确保解压后目录包含 Makefile 及全部源文件。提交前验证 tarball 内容完整性（`tar tzf libaio-libaio-0.3.113.tar.gz` 检查文件列表）。

### 方向 2（置信度: 中）
如果上游 libaio 的 pagure.io 归档内部目录名实际为 `libaio-libaio-0.3.113/`（而非 `libaio-0.3.113/`），则需要修正 `fix_getdeps.py` 第 3 步，将 manifest subdir **保持原值**（不修改，或修改为与 tarball 实际内部结构匹配的值）。即：先确定正确 tarball 的内部顶层目录名，再决定 subdir 是否需要修改。

### 方向 3（置信度: 低）
考虑通过 dnf 安装 libaio-devel 作为替代方案。在 Dockerfile 的 `dnf install` 步骤中补充 `libaio-devel`（如果 openEuler 24.03-LTS-SP3 仓库提供），结合 `--allow-system-packages` 参数让 getdeps 使用系统包而非从源码构建，彻底绕过 tarball 和 manifest 修复。

## 需要进一步确认的点
1. **tarball 内容验证**: 当前提交的 `libaio-libaio-0.3.113.tar.gz` 的实际内容是什么？解压后的 `libaio-0.3.113/` 目录下有哪些文件？需确认是缺少整个源码还是仅有 Makefile 缺失。
2. **上游 libaio 归档格式**: libaio 上游（pagure.io）对应 `libaio-0.3.113` tag 的 git archive 实际内部顶层目录名是什么（`libaio-libaio-0.3.113/` 还是 `libaio-0.3.113/`），以确定 `fix_getdeps.py` 的 subdir 修改是否正确。
3. **Boost cmake 冲突**: Boost `SEND_ERROR` 是否为独立失败点？需确认该 cmake 配置是否导致 getdeps 提前中止（log 中 `!! Failed` 出现在 338.7s，早于 libaio 的 339.0s）。需要排除 Boost 导入目标冲突是主要失败原因的可能性。
4. **getdeps fetcher.py 的 `_verify_hash` 签名**: `fix_getdeps.py` 第 2 步的正则是否能正确匹配 fbthrift v2026.06.29.00 源码中 `build/fbcode_builder/getdeps/fetcher.py` 的 `_verify_hash` 方法签名？若正则未命中，哈希校验未跳过，可能影响 libaio tarball 的提取验证流程。

## 修复验证要求
1. **code-fixer 必须从 fbthrift v2026.06.29.00 源码的 `build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的实际签名，验证 `fix_getdeps.py` 中正则是否能正确匹配后再提交。**
2. **code-fixer 必须从 libaio 官方仓库（https://pagure.io/libaio）的 `libaio-0.3.113` tag 获取正确归档，验证其解压后顶层目录名和内部文件结构（Makefile 存在性），再决定 subdir 修改策略。**
3. **code-fixer 需对 Boost SEND_ERROR 做独立评估：若 cmake 的 `message(SEND_ERROR ...)` 实际导致某依赖构建失败（非仅 libaio），需一并处理。**
