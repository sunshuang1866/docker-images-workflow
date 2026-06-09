# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: libaio 下载源失效
- 新模式症状关键词: pagure.io, Content-Type: text/html, libaio, getdeps.py, download, tar.gz, 2238 bytes

## 根因分析

### 直接错误
```
#11 411.5 Assessing libaio...
#11 411.5 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 411.5 .. 2238 of (Unknown)  [Complete in 2.811182 seconds]
#11 411.5 Content-Type: text/html; charset=utf-8
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build && ..." did not complete successfully: exit code: 1
------
Dockerfile:18
```

### 根因定位
- 失败位置: Dockerfile:18（`RUN git clone ... && ./build/fbcode_builder/getdeps.py ... build fbthrift`）
- 失败原因: `getdeps.py` 构建系统在构建 libaio 依赖时，尝试从 `pagure.io` 下载 `libaio-libaio-0.3.113.tar.gz`，但 pagure.io 返回的是 HTML 页面（仅 2238 字节，`Content-Type: text/html`）而非有效的 tar.gz 压缩包。尽管 PR 中 Dockerfile 预先 `cp` 了本地 libaio 文件到 downloads 目录，且 `fix_getdeps.py` 跳过了哈希校验，但 getdeps.py 仍然发起了网络下载，下载到的无效 HTML 文件导致后续解压/编译阶段失败。

### 与 PR 变更的关联
**直接由 PR 变更触发**。本次 PR 新增了 `Dockerfile` 和 `fix_getdeps.py` 两个文件：

1. **Dockerfile 的设计意图**：通过 `COPY libaio-libaio-0.3.113.tar.gz /tmp/libaio.tar.gz` 将本地 tarball 带入构建上下文，再 `cp` 到 getdeps 的 downloads 目录，期望 getdeps.py 识别已有文件并跳过下载。

2. **fix_getdeps.py 的补救措施不足**：该脚本只做了两件事 — (a) 添加 "openeuler" 到发行版识别列表，(b) 将 `_verify_hash` 方法替换为空操作以跳过哈希校验。但这并未阻止 getdeps.py 发起网络下载，也未能处理下载返回无效内容后的解压失败。

3. **根本矛盾**：pagure.io 上 libaio 的归档 tarball 已不可正常下载（返回 HTML），而 `fix_getdeps.py` 的补丁策略（仅跳过哈希校验）不足以绕过这一问题——因为问题出在"下载内容无效导致解压失败"，而非"哈希校验不通过"。

## 修复方向

### 方向 1（置信度: 高）
让 getdeps.py 完全跳过 libaio 的下载环节，直接使用预置的本地 tarball。需要在 `fix_getdeps.py` 中额外 patch getdeps 的 fetcher 逻辑，使其在检测到 downloads 目录下已存在对应文件时跳过下载步骤（或直接将 libaio 的下载 URL 替换为本地 file:// 路径）。当前仅跳过哈希校验不足以解决问题。

### 方向 2（置信度: 中）
检查 pagure.io 上 libaio 归档 tarball 的实际可用 URL 是否已变更，更新 getdeps 中 hardcoded 的下载 URL。但从日志中 HTML 响应（含 `techaro.lol-anubis-auth` cookie）来看，pagure.io 可能已经停止提供公开的归档下载或要求认证，换 URL 可能同样无效。

### 方向 3（置信度: 低）
在 getdeps 构建流程中完全移除 libaio 依赖（如果 fbthrift 2026.06.08.00 版本实际不需要 libaio），或在 Dockerfile 中直接通过系统包管理器安装 libaio（若 openEuler 仓库中有 `libaio-devel` 包）。

## 需要进一步确认的点
1. **pagure.io/libaio 归档状态**：需要确认 `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 是否已永久失效，以及是否有替代下载源。
2. **getdeps.py 的下载跳过逻辑**：需要查看 fbthrift 源码中 `build/fbcode_builder/getdeps/fetcher.py` 的完整逻辑，确认为什么预置到 downloads 目录的文件未被识别为"已下载"。
3. **libaio 是否为必需依赖**：确认 fbthrift v2026.06.08.00 是否绝对依赖 libaio，以及 openEuler 24.03-lts-sp3 仓库中是否有可用的 `libaio-devel` 系统包可替代源码编译。
4. **`fix_getdeps.py` 中 regex 替换的健壮性**：当前使用正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 来匹配并替换 `_verify_hash` 方法，若上游 getdeps 代码格式有变（如缩进不一致），该正则可能匹配失败，导致 patch 静默不生效。
