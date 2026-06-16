# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 上游源码下载链接失效
- 新模式症状关键词: text/html, Content-Type, pagure.io, libaio, getdeps, download, overwrite

## 根因分析

### 直接错误
```
#11 335.2 Assessing libaio...
#11 335.2 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 335.2 .. 2238 of (Unknown)  [Complete in 1.451916 seconds]
#11 335.2 Content-Type: text/html; charset=utf-8
#11 335.2 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 16 Jun 2026 08:36:22 GMT; Max-Age=0; Secure; SameSite=None
#11 335.2 Connection: close
#11 335.2 Transfer-Encoding: chunked

#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads &&     cp /tmp/libaio.tar.gz /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile`:18
- 失败原因: `pagure.io` 上 libaio 的下载链接（`https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz`）不再返回实际的 tar.gz 文件，而是返回 HTML 页面（`Content-Type: text/html`，大小 2238 字节）。getdeps.py 构建系统下载该 URL 后将 HTML 内容覆写了 Dockerfile 中预先拷贝的有效 libaio tar.gz，导致后续解压/校验步骤失败，整个构建退出码为 1。

### 与 PR 变更的关联
PR 新增了 fbthrift 2026.06.15.00 版本的完整构建链（Dockerfile、fix_getdeps.py、libaio tar.gz 二进制包）。PR 已经预见到 libaio 下载可能存在问题：
1. Dockerfile 预先 COPY 了 `libaio-libaio-0.3.113.tar.gz` 到容器内，并在 RUN 步骤中将文件拷贝到 getdeps 的 downloads 目录
2. `fix_getdeps.py` 修补了 `fetcher.py` 的 `_verify_hash` 方法（跳过哈希校验）

但 getdeps.py 构建系统在"Assessing libaio"阶段仍会无条件访问 pagure.io 下载 URL，并将返回的 HTML 页面覆写到 downloads 目录中预先放置的有效 tar.gz 文件。PR 的两个防御措施未能阻止 getdeps 重新下载并被错误内容覆盖，因此该失败**由本次 PR 的构建链设计缺陷直接触发**。

## 修复方向

### 方向 1（置信度: 高）
在 `fix_getdeps.py` 中增加对 libaio 下载步骤的拦截：修改 getdeps 的 manifest/fetcher 逻辑，使 libaio 的下载 URL 指向一个可用的镜像源（而非已失效的 pagure.io），或通过修改项目 fetcher.py 让 getdeps 在文件已存在时跳过下载（当前 fetcher.py 下载步骤是无条件的）。

### 方向 2（置信度: 中）
将 libaio 作为系统包通过 `dnf install` 安装（如 `libaio-devel`），并在 `getdeps.py` 调用时使用 `--allow-system-packages` 参数使构建系统使用系统提供的 libaio，从而完全绕过 getdeps 对 libaio 的源码下载和编译。需确认 openEuler 24.03-lts-sp3 仓库中 `libaio-devel` 版本是否与 fbthrift 2026.06.15.00 兼容。

## 需要进一步确认的点
- pagure.io 上 libaio 下载链接是否彻底失效还是临时故障。从日志返回的 HTML 响应判断（含 Set-Cookie、Content-Type: text/html），极可能是永久性失效（返回的是网页而非 404，可能是该归档已迁移或需要认证）
- fbthrift 的 getdeps manifest 中 libaio 的 URL 配置在哪个文件，确认是否可以在 fix_getdeps.py 中直接替换该 URL
- 确认 `libaio-devel` 在 openEuler 24.03-lts-sp3 中的可用性和版本兼容性
