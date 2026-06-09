# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 上游下载源失效
- 新模式症状关键词: Content-Type: text/html, pagure.io, tar.gz, Transfer-Encoding: chunked, libaio

## 根因分析

### 直接错误
```
#11 339.7 Assessing libaio...
#11 339.7 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 339.7 .. 2238 of (Unknown)  [Complete in 1.218867 seconds]
#11 339.7 Date: Tue, 09 Jun 2026 16:14:58 GMT
#11 339.7 Server: Apache/2.4.37 (Red Hat Enterprise Linux) OpenSSL/1.1.1k mod_wsgi/4.6.4 Python/3.6
#11 339.7 Content-Type: text/html; charset=utf-8
#11 339.7 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 09 Jun 2026 16:13:58 GMT; Max-Age=0; Secure; SameSite=None
#11 ERROR: process "/bin/sh -c git clone ... && ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/Dockerfile:18-23`（RUN 命令中的 getdeps 构建步骤）
- 失败原因: `pagure.io` 对 libaio 归档包的下载请求返回了 HTML 页面（`Content-Type: text/html`，仅 2238 字节）而非有效的 `.tar.gz` 二进制文件，getdeps 将无效的 HTML 内容当作 tar.gz 提取时失败。

### 与 PR 变更的关联
**直接关联**。本次 PR 新增了 fbthrift v2026.06.08.00 的 Dockerfile，构建过程通过 `getdeps.py` 自动拉取并编译 libaio 依赖。PR 作者已意识到 libaio 下载存在问题并尝试双重规避：
1. `COPY libaio-libaio-0.3.113.tar.gz /tmp/libaio.tar.gz` 将本地副本打入镜像上下文
2. `fix_getdeps.py` 中 patch `fetcher.py` 的 `_verify_hash` 方法为空操作以跳过哈希校验

但该规避方案未生效——`fix_getdeps.py` 仅跳过了哈希验证，未能阻止 getdeps 从 `pagure.io` 重新下载并将预置的有效文件覆盖为 HTML 内容。根因在于 `pagure.io` 源 URL 已失效/不可达（或该 libaio 版本在该源上不存在），getdeps 的 `ArchiveFetcher` 仍会执行实际下载动作。

## 修复方向

### 方向 1（置信度: 高）
修改 `fix_getdeps.py` 或在 Dockerfile 中增加对 getdeps fetcher 模块的 monkey-patch：在 `download` 方法层面拦截 libaio 的下载请求，使其在发现本地已存在有效文件时跳过网络下载，而不仅限于跳过哈希校验。或者直接修改 getdeps 的 manifest 中 libaio 的下载 URL 为可用源。

### 方向 2（置信度: 中）
将 `fix_getdeps.py` 的干预时机提前：在 getdeps 执行前更彻底地 patch `fetcher.py` 的 `download` 方法（而非仅 `_verify_hash`），或者在 `downloads` 目录放置文件后设置文件为不可写，防止被覆盖。但此方法依赖对 getdeps 内部实现的假设，较为脆弱。

## 需要进一步确认的点
1. `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 是否确实已失效（需浏览器/curl 验证），还是仅在 CI 构建环境中被拦截（如网络策略、IP 限制）
2. getdeps 的 `ArchiveFetcher.download()` 具体实现中是否在下载前检查本地文件存在性——如果确实检查了但文件名不匹配，需确认 getdeps 内部生成的目标文件名规则是否与 `libaio-libaio-libaio-0.3.113.tar.gz` 一致
3. libaio 的 `getdeps` manifest（`build/fbcode_builder/manifests/libaio`）中是否还有其他可用的下载 URL 可在不修改 getdeps 源码的情况下直接配置
