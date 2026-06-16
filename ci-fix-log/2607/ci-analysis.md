# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: libaio上游下载源失效
- 新模式症状关键词: pagure.io, text/html, Content-Type, Content-Length unknown, libaio, getdeps

## 根因分析

### 直接错误
```
#11 635.0 Assessing libaio...
#11 635.0 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 635.0 .. 2238 of (Unknown)  [Complete in 2.549555 seconds]
#11 635.0 Date: Tue, 16 Jun 2026 12:22:01 GMT
#11 635.0 Server: Apache/2.4.37 (Red Hat Enterprise Linux) OpenSSL/1.1.1k mod_wsgi/4.6.4 Python/3.6
#11 635.0 Content-Type: text/html; charset=utf-8
#11 635.0 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 16 Jun 2026 12:21:01 GMT; Max-Age=0; Secure; SameSite=None
#11 635.0 Connection: close
#11 635.0 Transfer-Encoding: chunked
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 ... && ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
------
Dockerfile:18
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile:18`（RUN 步骤中 getdeps.py 构建阶段）
- 失败原因: `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 下载返回的是 HTML 页面（`Content-Type: text/html; charset=utf-8`，仅 2238 字节），而非预期的 tar.gz 二进制包。Dockerfile 中预先 `cp` 到 downloads 目录的本地 libaio 文件未能阻止 getdeps 重新从上游下载，下载到的 HTML 内容导致后续解压/构建步骤失败。

### 与 PR 变更的关联
- **直接相关**：本次 PR 新增了整个 `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile` 和配套的 `fix_getdeps.py`。
- `fix_getdeps.py` 已尝试两个 workaround：① 添加 `"openeuler"` 到 getdeps 发行版识别列表；② 跳过 libaio 哈希校验（将 `_verify_hash` 替换为 `pass`）。但后者只绕过了校验步骤，**未阻止 getdeps 从上游重新下载**，因此预置到 downloads 目录的本地 `libaio.tar.gz` 被上游返回的 HTML 覆盖。
- `libaio-libaio-0.3.113.tar.gz`（二进制）是本次 PR 新增的本地文件，意图作为预缓存使用，但因上述原因未生效。

## 修复方向

### 方向 1（置信度: 高）
修改 `fix_getdeps.py`，在跳过哈希校验的同时，还需阻止 getdeps 的 fetcher 对 libaio 发起网络下载。具体为：在 `fetcher.py` 的下载方法中增加判断逻辑，当目标文件名已存在于 downloads 目录时跳过下载，或在 getdeps 的 manifest 中将 libaio 的下载源替换为本地 file:// 路径。确保预置的 `libaio.tar.gz` 能被直接使用而非被覆盖。

### 方向 2（置信度: 中）
验证 `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 是否为 libaio 0.3.113 的正确上游 URL。从响应头 `Set-Cookie: techaro.lol-anubis-auth=; Max-Age=0` 和 `Content-Type: text/html` 判断，pagure.io 可能已变更 URL 结构或该版本归档文件已下线。可尝试换用其他镜像源（如 GitHub mirrors）获取 libaio 0.3.113，或调整 URL 路径格式。

## 需要进一步确认的点
1. `pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 在当前是否仍为有效 URL（需浏览器直接访问验证）
2. getdeps.py 的 fetcher 源码中是否有"文件已存在则跳过下载"的逻辑，以及是否可通过环境变量或参数启用该行为
3. libaio 0.3.113 是否有其他可靠的上游下载源（如 GitHub release、其他镜像站）
4. `libaio-libaio-0.3.113.tar.gz` 本地文件是否确实与 fbthrift 2026.06.15.00 版本兼容（版本/内容是否正确）
