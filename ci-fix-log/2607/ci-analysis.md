# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 上游源码站鉴权拦截
- 新模式症状关键词: pagure.io, Content-Type: text/html, Set-Cookie, libaio, getdeps

## 根因分析

### 直接错误

```
#11 348.3 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> .../downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 348.3 .. 2238 of (Unknown)  [Complete in 1.192612 seconds]
#11 348.3 Content-Type: text/html; charset=utf-8
#11 348.3 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 16 Jun 2026 00:27:36 GMT; Max-Age=0; Secure; SameSite=None
#11 348.3 Connection: close
#11 348.3 Transfer-Encoding: chunked
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} ... && ./build/fbcode_builder/getdeps.py ... build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:18 (RUN 指令)
- 失败原因: fbthrift 构建依赖 libaio，getdeps 从 `pagure.io` 下载 libaio 源码时，pagure.io 返回了 HTML 认证页面（仅 2238 字节）而非二进制 tar.gz 包，导致后续解压/构建步骤失败。

### 与 PR 变更的关联

**高度关联**。PR 新增了 `fix_getdeps.py` 脚本，通过预拷贝 libaio tarball 并绕过哈希校验来规避上游下载问题。但该脚本存在两个潜在缺陷，导致规避未生效：

1. **`_verify_hash` 正则 patch 可能静默失败**：`fix_getdeps.py` 使用的正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 依赖于 `_verify_hash` 后紧跟一个 4 空格缩进的 `def` 行。若上游 `fetcher.py` 中该方法之后是不同缩进层级的代码（如嵌套函数、类结束等），则 `re.sub` 不匹配、无报错返回原内容，`_verify_hash` 未被 patch。getdeps 校验预拷贝文件的哈希失败后即从 pagure.io 重新下载，得到 HTML 页面。

2. **pagure.io 归档下载返回 HTML**：`https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 返回 `Content-Type: text/html` 并带有认证 Cookie，表明该 URL 指向的是鉴权拦截页而非真正的归档制品。即使没有正则 patch 问题，若预拷贝文件能通过 hash 校验也存在风险——一旦 getdeps 决定重新下载就会被 HTML 覆盖。

## 修复方向

### 方向 1（置信度: 高）
将 `fix_getdeps.py` 中对 `_verify_hash` 的 patch 方式从正则替换改为更稳健的方案。当前正则依赖 `_verify_hash` 方法之后恰好有一个 4 空格缩进的 `def` 行，若上游代码结构不符合此假设则静默失败。建议改用整方法替换（匹配 `def _verify_hash` 到下一个同缩进级别的 `def`）或在 Python 层面通过 monkey-patching 运行时替换该方法，避免正则不匹配时的静默失败。

### 方向 2（置信度: 中）
在预拷贝 libaio tarball 之后、执行 getdeps 之前，将 `pagure.io` 的下载 URL 替换为一个本地 file:// 协议或禁用对 libaio 的网络 fetch，确保 getdeps 必然使用预置的本地文件而不触发远程下载。

### 方向 3（置信度: 低）
确认 pagure.io 的 libaio 归档 URL 是否已变更（如改为 `https://releases.pagure.org/libaio/libaio-0.3.113.tar.gz`），如果上游 URL 格式已更新，更新 getdeps manifest 中的下载地址即可。

## 需要进一步确认的点
1. 在 CI Runner 环境中实际读取 `build/fbcode_builder/getdeps/fetcher.py` 的 `_verify_hash` 方法上下文代码，确认 `fix_getdeps.py` 的正则是否能正确匹配并完成替换。
2. 确认 pagure.io 当前对匿名归档下载是否需要认证（可直接 curl 测试该 URL 的响应状态码和 Content-Type）。
3. 确认预拷贝的 tarball 文件格式是否正确（`file /tmp/libaio.tar.gz` 确认确实是 gzip 压缩包而非其他格式）。
