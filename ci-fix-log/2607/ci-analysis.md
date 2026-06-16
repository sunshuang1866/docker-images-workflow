# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: getdeps缓存文件名不匹配
- 新模式症状关键词: libaio, getdeps, downloads, filename mismatch, pagure.io, text/html, Content-Type

## 根因分析

### 直接错误
```
#11 336.1 Assess libaio...
#11 336.1 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 336.1 .. 2238 of (Unknown)  [Complete in 1.222425 seconds]
#11 336.1 Content-Type: text/html; charset=utf-8
#11 336.1 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=...
#11 336.1 Transfer-Encoding: chunked
...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads &&     cp /tmp/libaio.tar.gz /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-0.3.113.tar.gz &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:18（`RUN` 构建步骤）
- 失败原因: Dockerfile 中 `cp` 的目标文件名 `libaio-libaio-0.3.113.tar.gz` 与 getdeps 框架期望的缓存文件名 `libaio-libaio-libaio-0.3.113.tar.gz` 不匹配，导致预置的本地 tarball 未被命中，getdeps 回退到网络下载 pagure.io 上的 libaio 源码包。而 pagure.io 对该 URL 返回了 HTML 页面（`Content-Type: text/html`，含 `Set-Cookie`），下载到的内容并非有效的 tar.gz 归档，getdeps 解压/校验失败，最终 `exit code: 1`。

### 与 PR 变更的关联
- 本次 PR 新增了 `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile`，其中在 RUN 步骤中向 getdeps downloads 目录拷贝 libaio 源码包时，使用的目标文件名 `libaio-libaio-0.3.113.tar.gz` 与 getdeps 实际下载时构造的本地缓存文件名 `libaio-libaio-libaio-0.3.113.tar.gz` 相差一个 `libaio-` 前缀（getdeps 在缓存文件名前额外拼接了包名 `libaio-`）。这是本次 PR 引入的构建逻辑缺陷，文件名由 PR author 手动指定，拼写与 getdeps 内部规则不一致。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 第 21 行 `cp` 命令的目标文件名从 `libaio-libaio-0.3.113.tar.gz` 修正为 `libaio-libaio-libaio-0.3.113.tar.gz`（在 `libaio-` 前缀与版本号之间补一个 `libaio-`），使预置的本地 tar.gz 与 getdeps 缓存查找路径一致，从而跳过失败的 pagure.io 网络下载。

## 需要进一步确认的点
- 确认 pagure.io 上 `libaio-0.3.113` 归档是否仍然可用（本次下载返回 HTML 说明该端点可能已失效或需认证），若已永久失效则依赖本地预置文件的策略是正确的，仅需修正文件名匹配。
- 确认 `fix_getdeps.py` 中跳过 `_verify_hash` 的 patch 是否完全生效——本次失败发生在下载/解压阶段而非哈希校验阶段，故该 patch 本身不是根因，但需验证修好文件名后哈希跳过逻辑仍正常工作。
