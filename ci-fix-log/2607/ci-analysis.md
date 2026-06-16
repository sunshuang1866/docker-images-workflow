# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: getdeps覆盖预置下载
- 新模式症状关键词: `pagure.io`, `Content-Type: text/html`, `libaio`, `Set-Cookie`, `getdeps`, `overwrite`

## 根因分析

### 直接错误
```
#11 334.8 Assessing libaio...
#11 334.8 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 334.8 .. 2238 of (Unknown)  [Complete in 1.245137 seconds]
#11 334.8 Date: Tue, 16 Jun 2026 23:03:48 GMT
#11 334.8 Server: Apache/2.4.37 (Red Hat Enterprise Linux) OpenSSL/1.1.1k mod_wsgi/4.6.4 Python/3.6
#11 334.8 Content-Type: text/html; charset=utf-8
#11 334.8 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 16 Jun 2026 23:02:48 GMT; Max-Age=0; Secure; SameSite=None
#11 334.8 Connection: close
#11 334.8 Transfer-Encoding: chunked
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} ... && ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile:18`（RUN 指令中的 getdeps.py 构建步骤）
- 失败原因: pagure.io 对 libaio 归档包的请求返回了 HTML 页面（Content-Type: text/html，仅 2238 字节，含有 Set-Cookie 头）而非实际的 tar.gz 文件，getdeps 将此无效 HTML 内容当作 tarball 写入 downloads 目录，覆盖了 Dockerfile 中预先 COPY 的正确文件，导致后续解压/构建失败。

### 与 PR 变更的关联
PR 新增了 fbthrift v2026.06.15.00 的 Dockerfile 及其配套文件。PR 作者已意识到 libaio 的下载问题，尝试通过两个手段规避：
1. **预置 tarball**：将 `libaio-libaio-0.3.113.tar.gz` 作为二进制文件提交到仓库，并在 Dockerfile 中 COPY 到 getdeps 的 downloads 目录
2. **跳过哈希校验**：`fix_getdeps.py` 中 patch 了 `fetcher.py` 的 `_verify_hash` 方法为空操作

但修复不完整：`fix_getdeps.py` 仅跳过了哈希校验，**未阻止 getdeps 在文件已存在时重新下载**。getdeps 的下载步骤会覆盖预置的正确文件，而 pagure.io 当前返回的 HTML 内容无法作为有效的 tarball 使用。

## 修复方向

### 方向 1（置信度: 高）
修改 `fix_getdeps.py`，在 patch 哈希校验的同时，额外 patch getdeps 的下载逻辑：当 downloads 目录中目标文件已存在时跳过下载步骤。或者直接在 Dockerfile 的 RUN 指令中，在调用 getdeps.py 之前将预置的 tar.gz 设置为只读，阻止 getdeps 覆盖。

### 方向 2（置信度: 中）
将 libaio 的下载源从 pagure.io 替换为其他可用镜像（如 GitHub mirros 或本地 HTTP 服务），在 `fix_getdeps.py` 中 patch getdeps 的 manifest 配置，将 libaio 的 URL 指向可靠源。此方向需要先确认 libaio-0.3.113 在其他镜像站的可用性。

## 需要进一步确认的点
1. pagure.io/libaio 是否已永久停止提供直接下载，或仅为临时故障——这决定了方向 1 的修复是否为长期方案
2. 预置的 `libaio-libaio-0.3.113.tar.gz` 文件内容是否正确完整——需确认该二进制文件未被截断或损坏
3. fbthrift 上游 `getdeps.py` 的下载逻辑中是否存在"文件已存在则跳过下载"的选项或参数——若有，可直接利用而无需额外 patch
