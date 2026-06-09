# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 下载源返回HTML非二进制包
- 新模式症状关键词: `Content-Type: text/html`, `Set-Cookie`, `pagure.io`, `chunked`, `tar.gz`

## 根因分析

### 直接错误
```
#11 341.3 Assessing libaio...
#11 341.3 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> .../downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 341.3 .. 2238 of (Unknown)  [Complete in 1.195109 seconds]
#11 341.3 Date: Tue, 09 Jun 2026 18:01:10 GMT
#11 341.3 Content-Type: text/html; charset=utf-8
#11 341.3 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 09 Jun 2026 18:00:10 GMT; Max-Age=0; Secure; SameSite=None
#11 341.3 Connection: close
#11 341.3 Transfer-Encoding: chunked
#11 341.3
#11 341.3
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:18（RUN 命令中 getdeps.py build fbthrift 步骤的 libaio 下载阶段）
- 失败原因: `pagure.io` 对 libaio 源码包的下载请求返回了 HTML 页面（含 `Set-Cookie` 认证头），而非预期的 `tar.gz` 二进制文件。getdeps 下载了 2238 字节的 HTML 内容并覆盖了 PR 中预置的本地 `libaio-libaio-0.3.113.tar.gz` 副本，后续提取 tar.gz 时失败导致整个构建命令以 exit code 1 退出。

### 与 PR 变更的关联

**直接关联**。本次 PR 新增了 fbthrift v2026.06.08.00 的 Dockerfile 及配套文件。Dockerfile 中设计了"预置本地 libaio 包 + 修补 `_verify_hash` 为 `pass`"的策略来绕过外网下载问题，但该策略存在两个缺陷：

1. **下载未阻止**：`fix_getdeps.py` 仅修补了 `_verify_hash` 方法使之跳过哈希校验，但未阻止 getdeps 的 fetcher 从远程 URL 重新下载文件。getdeps 在 libaio 的 `assess`/`download` 阶段仍会发起 HTTP 请求，下载到的 HTML 内容覆盖了 Dockerfile 中 `cp` 命令预先放置的正确 tar.gz。

2. **pagure.io 认证墙**：CI 构建环境访问 `pagure.io/libaio/archive/...` 时，`pagure.io` 返回了带认证 Cookie（`techaro.lol-anubis-auth`）的 HTML 页面而非实际 tar.gz，表明该源站对匿名/CI 请求有认证拦截，已无法作为可用的直接下载源。

## 修复方向

### 方向 1（置信度: 高）
修改 `fix_getdeps.py`，在修补 `_verify_hash` 的同时，额外修补 fetcher 的下载方法（如 `_download` 或 `download`），使其在检测到 downloads 目录下文件已存在时跳过远程下载，直接使用本地文件。这样可以确保 Dockerfile 中预置的本地 `libaio` 包不会被远程 HTML 响应覆盖。

### 方向 2（置信度: 中）
如果 `pagure.io` 的 libaio 下载 URL 格式已变更或该源已停用，需在 fbthrift 源码的 getdeps manifest（`build/fbcode_builder/manifests/libaio`）中将下载 URL 更换为其他可用镜像源（如 GitHub releases 或 openEuler 内部镜像），或直接将 libaio 源码包以 `COPY` 方式提供并跳过整个 download 阶段。

## 需要进一步确认的点
1. 确认 `pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 在浏览器中直接访问是否也返回 HTML（确认是否为 CI IP 被限或全站认证墙）。
2. 确认 `fix_getdeps.py` 中针对 `_verify_hash` 的正则替换是否确实生效——若 `_verify_hash` 是 fetcher 类的最后一个方法（后续无 `def`），正则 `(?=\n    def )` 可能匹配失败，导致哈希校验未被跳过，叠加本地文件哈希不匹配进一步触发重新下载。
3. 确认是否有其他可用的 libaio 源码镜像源可替代 `pagure.io`。
