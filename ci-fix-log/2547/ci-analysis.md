# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 上游归档URL失效
- 新模式症状关键词: Content-Type: text/html, pagure.io, libaio, tar.gz download corrupt, Set-Cookie, techaro.lol-anubis-auth

## 根因分析

### 直接错误
```
#11 339.7 Assessing libaio...
#11 339.7 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz
#11 339.7 .. 2238 of (Unknown)  [Complete in 1.215876 seconds]
#11 339.7 Date: Tue, 09 Jun 2026 12:28:21 GMT
#11 339.7 Server: Apache/2.4.37 (Red Hat Enterprise Linux) OpenSSL/1.1.1k mod_wsgi/4.6.4 Python/3.6
#11 339.7 Content-Type: text/html; charset=utf-8
#11 339.7 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 09 Jun 2026 12:27:21 GMT; Max-Age=0; Secure; SameSite=None
#11 339.7 Connection: close
#11 339.7 Transfer-Encoding: chunked
#11 339.7 
#11 ERROR: process "... ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
------
Dockerfile:18
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/Dockerfile:18`
- 失败原因: getdeps.py 构建过程中尝试从 `https://pagure.io/libaio/archive/libaio-0.3.113/` 下载 libaio 依赖，但上游 URL 返回了 HTML 页面（Content-Type: text/html，仅 2238 字节）而非 tar.gz 归档文件。HTML 页面触发了 `techaro.lol-anubis-auth` 认证 Cookie 设置，表明该 URL 可能已失效或需要认证。getdeps 下载到本地的 "tar.gz" 实际上是 HTML 页面，导致后续构建步骤（解压/编译）失败。

### 与 PR 变更的关联
- **由 PR 直接触发**：该 PR 新增了 fbthrift 2026.06.08.00 的完整 Dockerfile 和构建脚本。虽然 PR 中已预置了 `libaio-libaio-0.3.113.tar.gz` 二进制文件并通过 `COPY` 预拷贝到 downloads 目录，但 `getdeps.py` 在运行时仍会重新下载该文件并**覆盖**预置的本地副本。覆盖后的文件实际为 HTML 页面，导致构建失败。
- PR 中的 `fix_getdeps.py` 已尝试绕过哈希校验（跳过 `_verify_hash`），但未解决下载源失效的问题。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 中，`cp` 预拷贝 libaio.tar.gz 后，额外创建标记文件或修改文件权限为只读，让 getdeps 跳过下载步骤（取决于 getdeps 的 fetcher 是否有"文件已存在则跳过"的逻辑）。或者，直接禁用 getdeps 对 libaio 的网络下载（修改 fetcher.py 中 libaio 的下载逻辑，如果文件已存在则直接返回）。

### 方向 2（置信度: 中）
将 libaio 的下载源从 `pagure.io` 替换为其他可用镜像源，或修改为从 GitHub releases / Gitee 等其他可靠源下载。需确认 libaio 0.3.113 版本在其他源上的可用性。

### 方向 3（置信度: 低）
在 `fix_getdeps.py` 中额外 patch getdeps 的 libaio manifest 配置，将 download URL 替换为有效的源，或直接跳过 libaio 的下载/构建步骤（如果系统已通过 dnf 安装了等效库则可用 `--allow-system-packages` 绕过）。

## 需要进一步确认的点
1. `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 为何返回 HTML 而非归档文件 —— 是临时故障还是该归档已永久移除；`techaro.lol-anubis-auth` 表明可能被重定向到认证网关。
2. getdeps 的 fetcher 在目标文件已存在时的行为 —— 是否会跳过下载，还是无条件覆盖。如果会跳过，则预拷贝文件的路径或文件名可能不匹配 getdeps 内部计算的文件名。
3. 日志中未显示 getdeps 抛出具体错误类型（如 "Failed to extract archive"、"Checksum mismatch"、"No such file"），只显示了 `exit code: 1`，需要获取更完整的构建日志以确认最终致命错误的确切位置。
