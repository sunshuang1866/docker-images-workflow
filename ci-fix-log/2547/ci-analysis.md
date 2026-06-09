# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: pagure.io下载鉴权重定向
- 新模式症状关键词: pagure.io, Content-Type: text/html, Set-Cookie, libaio, getdeps, chunked, Transfer-Encoding

## 根因分析

### 直接错误

```
#11 344.1 Assessing libaio...
#11 344.1 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 344.1 .. 2238 of (Unknown)  [Complete in 1.312054 seconds]
#11 344.1 Content-Type: text/html; charset=utf-8
#11 344.1 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 09 Jun 2026 18:46:18 GMT; Max-Age=0; Secure; SameSite=None
#11 344.1 Connection: close
#11 344.1 Transfer-Encoding: chunked
#11 344.1
#11 344.1
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build && ... && python3 /tmp/fix_getdeps.py && ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
------
Dockerfile:18
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/Dockerfile:18`（RUN 步骤中的 getdeps 构建流程）
- 失败原因: pagure.io 对 libaio 下载请求返回 HTML 鉴权/登录页面（`Content-Type: text/html`、`Set-Cookie`），而非实际的 tar.gz 压缩包。getdeps 下载此 HTML 内容后覆写了 `fix_getdeps.py` 修补前通过 `cp` 预置的本地 libaio 压缩包，导致后续提取（extract）阶段处理无效归档文件而失败。

### 与 PR 变更的关联

**强关联。** 本次 PR 新增的 `Dockerfile`（`Others/fbthrift/2026.06.08.00/24.03-lts-sp3/Dockerfile`）和 `fix_getdeps.py` 是触发该构建流程的直接来源。

PR 的 `fix_getdeps.py` 已尝试两种缓解手段：
1. `cp /tmp/libaio.tar.gz` 到 getdeps 的 downloads 目录（预置本地副本）
2. 修补 `_verify_hash` 方法跳过哈希校验（避免校验失败阻断流程）

但这两项措施未能阻止 getdeps 从 pagure.io 实际发起下载——getdeps 在"Assessing libaio"阶段仍会尝试远程下载，并使用 HTTP 响应内容（HTML 页面）覆写 downloads 目录中预置的有效 tar.gz 文件。由于 `_verify_hash` 已被修补为 `pass`，校验不会报错，但后续对 HTML 内容的 tar 解压操作失败，导致整个 RUN 步骤以 exit code 1 退出。

## 修复方向

### 方向 1 — 阻止 getdeps 远程下载 libaio（置信度: 高）
在 `fix_getdeps.py` 中增加对 libaio 下载源的干预——修补 getdeps 的 manifest/recipes 文件，将 libaio 的下载 URL 从 pagure.io 改为指向本地已预置的文件（`file:///tmp/libaio.tar.gz`），使 getdeps 在 "Assessing libaio" 阶段直接使用本地副本而无需发起远程 HTTP 请求。同时保留现有的 `_verify_hash` 跳过修补和 `cp` 预置逻辑。

### 方向 2 — 换用其他可访问的 libaio 源（置信度: 中）
在 `fix_getdeps.py` 中修补 getdeps 的 libaio 下载 URL，将 `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 替换为 GitHub mirror 或其他无需鉴权即可获取的镜像源（如 `https://github.com/linux-rdma/libaio/archive/refs/tags/libaio-0.3.113.tar.gz` 或 `https://releases.pagure.org/libaio/libaio-0.3.113.tar.gz`），避免 pagure.io 鉴权重定向。

## 需要进一步确认的点
1. pagure.io 对 libaio 的鉴权重定向是否为新增行为或临时性问题（可通过浏览器直接访问该 URL 确认）。
2. getdeps 内部是否提供了"跳过下载、仅使用本地缓存"的机制（如 `--no-download` 或环境变量 `GETDEPS_USE_CACHE=1`）——若有，可优先采用而非修补源码。
3. 预置的 `libaio-libaio-0.3.113.tar.gz` 本地文件是否与 fbthrift 构建要求的版本完全匹配（需核对 SHA 或内容）。
