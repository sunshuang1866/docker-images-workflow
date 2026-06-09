# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 预置文件未能阻止下载
- 新模式症状关键词: `Content-Type: text/html`, `pagure.io`, `libaio`, `Download with`, `_verify_hash`

## 根因分析

### 直接错误
```
#11 339.9 Assessing libaio...
#11 339.9 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 339.9 .. 2238 of (Unknown)  [Complete in 1.241359 seconds]
#11 339.9 Date: Tue, 09 Jun 2026 17:15:26 GMT
#11 339.9 Server: Apache/2.4.37 (Red Hat Enterprise Linux) OpenSSL/1.1.1k mod_wsgi/4.6.4 Python/3.6
#11 339.9 Content-Type: text/html; charset=utf-8
#11 339.9 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 09 Jun 2026 17:14:26 GMT; ...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 ..." did not complete successfully: exit code: 1
------
Dockerfile:18
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/Dockerfile:18`
- 失败原因: `getdeps.py` 构建 fbthrift 时尝试从 `pagure.io` 下载 libaio 依赖，服务器返回了 HTML 页面（`Content-Type: text/html`）而非 tar.gz 归档文件，导致下载/解压失败，构建退出码为 1。

### 详细分析

1. **时序回顾**：构建流程中，`gflags`（GitHub）、`glog`（GitHub）、`googletest`（GitHub）等依赖均下载成功，响应头为 `Content-Type: application/x-gzip`。运行至 libaio 时，`pagure.io` 返回 `Content-Type: text/html; charset=utf-8`，仅收到 2238 字节（对比 googletest 的 885595 字节），明显是 HTML 错误页面而非真实归档包。

2. **预置文件策略为何未生效**：PR 在 Dockerfile 中通过 `COPY` 将本地 `libaio-libaio-0.3.113.tar.gz` 预置到 `/tmp/libaio.tar.gz`，再 `cp` 到 getdeps 的 downloads 目录，并配合 `fix_getdeps.py` 修补 `_verify_hash` 为 no-op 以绕过哈希校验。然而日志显示 getdeps **仍然执行了下载操作**。可能原因：
   - `fix_getdeps.py` 中修改 `_verify_hash` 的**正则表达式未能匹配**实际 `fetcher.py` 源码中的方法体（缩进格式、行尾换行符差异，或该方法为类内最后方法时没有后续 `def` 作为锚点），导致替换未生效，getdeps 因哈希不匹配而重新下载。
   - 即使哈希修补生效，getdeps 的 `download()` 流程可能**不检查文件是否已存在**，总是先从远程拉取，`_verify_hash` 只用于下载后验证。此时预置文件会被远程下载的 HTML 内容覆盖。

3. **pagure.io 返回 HTML 的原因**：日志中响应包含 `Set-Cookie` 头，且无 `Content-Length`，暗示该 URL 可能触发了 pagure.io 的认证/重定向页面，或者标签 `libaio-0.3.113` 在该仓库中不存在（404 但以 HTML 页面形式返回）。

### 与 PR 变更的关联
- **直接关联**：PR 新增了 `Dockerfile`（`Dockerfile:18`）和 `fix_getdeps.py`，构建失败发生在 Dockerfile 中定义的 `RUN` 步骤内。若该 PR 未合并，此构建流水线不会被触发。
- **非 PR 代码逻辑错误**：失败的根本原因是外部依赖下载源（`pagure.io`）返回了非预期内容，以及 `fix_getdeps.py` 的哈希绕过策略未能阻止远程下载。这不是 Dockerfile 中 `dnf install` 列表遗漏或版本号错误等典型问题。
- **新版本触发**：作为自动升级 PR（`v2026.06.08.00`），失败可能在该版本首次构建时暴露，但不排除旧版本同样存在此问题（取决于 `pagure.io` 的 URL 在下游构建 job 中的历史可用性）。

## 修复方向

### 方向 1（置信度: 中）
**确保预置的 libaio tarball 被 getdeps 识别并跳过下载**。需验证 `fix_getdeps.py` 中 `_verify_hash` 的正则替换在目标 `fetcher.py` 版本中是否正确匹配。若不匹配，需根据实际 `fetcher.py` 源码调整正则或改用其他方式（如直接修改 `Fetcher` 类的 `download` 方法，在下载前检查本地文件是否存在且有效）。同时确认 `fetcher.py` 的 `download` 流程是否支持"文件已存在则跳过"的逻辑——若不支持，仅修改 `_verify_hash` 不足以阻止下载。

### 方向 2（置信度: 低）
**更换 libaio 下载源**。如果 `pagure.io/libaio/archive/` 持续返回 HTML（例如该仓库归档策略变更），可考虑在 getdeps 的 manifest 中将 libaio 源替换为其他镜像或直接使用本地文件路径（`file://` scheme），完全绕过远程下载。

### 方向 3（置信度: 低）
**使用 dnf 系统包替代源码编译**。检查 openEuler 24.03-lts-sp3 仓库是否提供 `libaio-devel` 包，若提供则可在 `dnf install` 步骤中添加，并通过 getdeps 的 `--allow-system-packages` 标志让构建使用系统预装的 libaio，从而跳过下载和编译步骤。

## 需要进一步确认的点
1. **【优先级高】确认 `pagure.io` URL 的实际状态**：在构建环境外直接访问 `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz`，检查返回的是归档文件还是 HTML 页面，以及 HTTP 状态码（200/302/404）。
2. **验证 `fix_getdeps.py` 正则替换的有效性**：在目标 fbthrift 版本（`v2026.06.08.00`）对应的 `build/fbcode_builder/getdeps/fetcher.py` 中检查 `_verify_hash` 方法的实际代码结构，确认正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 能否成功匹配并替换。
3. **确认 getdeps `download` 流程的跳过逻辑**：阅读 `fetcher.py` 的 `download()` / `_download()` 方法，判断是否在下载前检查文件已存在且有有效哈希——若不存在此逻辑，仅修补 `_verify_hash` 无法阻止远程下载。
4. **对比历史成功构建**：检查 fbthrift 上一个版本（`v2026.05.18.00`）的构建是否也曾依赖 `pagure.io` 下载 libaio，以及当时是否成功。这有助于判断本次失败是 pagure.io 的临时故障还是 URL 永久失效。
