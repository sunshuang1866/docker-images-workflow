# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式 (无完全匹配的历史模式)
- 新模式标题: 上游下载源返回HTML
- 新模式症状关键词: Content-Type: text/html, libaio, pagure.io, tar.gz response, Set-Cookie, anubis-auth

## 根因分析

### 直接错误

```
#11 340.2 Assessing libaio...
#11 340.2 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 340.2 .. 2238 of (Unknown)  [Complete in 1.691271 seconds]
#11 340.2 Date: Tue, 09 Jun 2026 15:05:49 GMT
#11 340.2 Server: Apache/2.4.37 (Red Hat Enterprise Linux) OpenSSL/1.1.1k mod_wsgi/4.6.4 Python/3.6
#11 340.2 X-Xss-Protection: 1; mode=block
#11 340.2 X-Content-Type-Options: nosniff
#11 340.2 Referrer-Policy: same-origin
#11 340.2 X-Frame-Options: ALLOW-FROM https://pagure.io/
#11 340.2 Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
#11 340.2 Content-Type: text/html; charset=utf-8
#11 340.2 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 09 Jun 2026 15:04:49 GMT; Max-Age=0; Secure; SameSite=None
#11 340.2 Connection: close
#11 340.2 Transfer-Encoding: chunked
```

随后构建立即退出:
```
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build && ..." did not complete successfully: exit code: 1
```

### 根因定位

- 失败位置: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/Dockerfile:18-23` (RUN 步骤中的 getdeps.py 构建阶段)
- 失败原因: **pagure.io 对 libaio 归档下载请求返回了 HTML 页面（`Content-Type: text/html`）而非 tar.gz 压缩包**，大小仅 2238 字节，且响应中包含 `Set-Cookie: techaro.lol-anubis-auth=` 等鉴权/WAF 相关头，表明 pagure.io 对该 URL 实施了访问拦截或要求认证。getdeps.py 将此 HTML 文件当作 libaio 归档尝试解压，导致构建退出码为 1。

### 与 PR 变更的关联

**PR 变更直接触发了此失败**，但非代码逻辑错误所致。PR 新增的 Dockerfile 设计思路正确——通过预先 `COPY libaio-libaio-0.3.113.tar.gz /tmp/libaio.tar.gz` 并 `cp` 到 getdeps 的 downloads 目录来绕过上游下载。同时 `fix_getdeps.py` 试图通过 patch `_verify_hash` 方法跳过哈希校验，使预置的本地 tarball 能被接受。

但实际执行中，getdeps.py **仍然访问了 pagure.io 并下载了 HTML 页面**，覆盖或取代了预置的本地 tarball。两个可能原因叠加:

1. **`fix_getdeps.py` 中 `_verify_hash` 的 regex patch 未成功匹配**：正则表达式 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 依赖 `_verify_hash` 之后存在另一个以 4 空格缩进的 `def ` 方法作为前瞻锚点。如果 `_verify_hash` 是类中最后一个方法，或缩进格式不精确匹配，该正则不会匹配任何内容，导致哈希校验未被禁用，预置 tarball 因哈希不匹配被拒绝。

2. **pagure.io 不再直接提供该版本的 libaio 归档下载**，返回认证/WAF 拦截页面而非二进制文件。

## 修复方向

### 方向 1（置信度: 高）
**修复 `fix_getdeps.py` 中 `_verify_hash` 的 patch 逻辑**，确保补丁在任何情况下都能正确移除哈希校验。当前正则使用了不稳定的前瞻锚点（依赖后续方法存在）。应改用更稳健的替换方式——例如匹配整个 `_verify_hash` 方法体直到下一个同缩进级别的方法或类结束，或直接从文件层面删除该校验调用。

### 方向 2（置信度: 中）
**调查 pagure.io libaio 归档 URL 的正确性**。当前 URL `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 返回 HTML，可能需要：
- 确认该 tag (`libaio-0.3.113`) 在 pagure.io 上是否存在
- 检查正确的归档下载 URL 格式
- 考虑是否因 CI 网络环境被 pagure.io WAF 拦截

### 方向 3（置信度: 低）
如果 pagure.io 下载源持续不可用，可考虑将 libaio 完全作为本地依赖处理——确保 `fix_getdeps.py` 的哈希绕过生效后，getdeps.py 直接使用预置的 `/tmp/libaio.tar.gz`，无需任何网络请求。

## 需要进一步确认的点
1. **fix_getdeps.py 的 regex 是否实际生效**：需确认目标文件 `build/fbcode_builder/getdeps/fetcher.py` 中 `_verify_hash` 方法的实际缩进格式及是否为其类中最后一个方法。如果前瞻锚点未匹配，该补丁是空操作，这是最可能的问题点。
2. **pagure.io 归档 URL 是否有效**：在 CI 环境外手动访问该 URL，确认其是否返回有效的 tar.gz 还是 HTML。如果 URL 本身已失效，方向 1 修复后仍需验证本地 tarball 能否被正确接受。
3. **预置 tarball 的文件名是否完全匹配**：getdeps.py 期望的下载文件名与实际 cp 的目标文件名是否完全一致（注意路径中有 `libaio-libaio-libaio-0.3.113.tar.gz`，包含两个 `libaio`）。
