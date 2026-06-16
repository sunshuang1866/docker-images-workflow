# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: getdeps下载覆盖预置tar包
- 新模式症状关键词: pagure.io, text/html, libaio, Content-Type, getdeps, download, 2238 bytes

## 根因分析

### 直接错误
```
#11 334.5 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 334.5 .. 2238 of (Unknown)  [Complete in 1.235021 seconds]
#11 334.5 Content-Type: text/html; charset=utf-8
#11 334.5 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 16 Jun 2026 04:19:06 GMT; Max-Age=0; Secure; SameSite=None
#11 334.5 Connection: close
#11 334.5 Transfer-Encoding: chunked
#11 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

getdeps.py 从 `pagure.io` 下载 libaio 依赖时，服务器返回的是 HTML 页面（`Content-Type: text/html`，2238 字节），而非实际的 tar.gz 归档文件。随后 getdeps.py 尝试解压该 HTML 文件作为 tar.gz 失败，导致整个 RUN 命令以 exit code 1 退出。

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile`:18（RUN 命令）
- 失败原因: `pagure.io` 上 libaio 归档 URL 不再返回有效的 tar.gz 文件（返回 HTML 错误/登录页面），且 fix_getdeps.py 仅跳过了哈希校验（`_verify_hash`），未能阻止 getdeps.py 发起实际下载并覆盖预置的合法 libaio.tar.gz

### 与 PR 变更的关联
本 PR 新增了 3 个文件，构成了完整的 fbthrift 构建链路：
1. **Dockerfile** — 定义构建步骤，包括用 `cp` 将本地 `libaio-libaio-0.3.113.tar.gz` 预置到 getdeps 下载目录，然后运行 `fix_getdeps.py` 打补丁，最后执行 `getdeps.py build fbthrift`
2. **fix_getdeps.py** — 修补 `getdeps_platform.py` 添加 `openeuler` 发行版识别，修补 `fetcher.py` 将 `_verify_hash` 替换为空操作（跳过哈希校验）
3. **libaio-libaio-0.3.113.tar.gz** — 本地预置的 libaio 源码包

问题根源：fix_getdeps.py 的补丁策略（跳过哈希校验 + 预置 tar 包）不足以阻止 getdeps.py 重新从网络下载 libaio。getdeps.py 的下载逻辑在发现预置文件后仍会发起实际 HTTP 下载，覆盖预置文件，而 `pagure.io` 此时返回的是 HTML 错误页面，导致后续解压/构建步骤失败。getdeps.py 在此之前的其他依赖（boost、glog、fmt、gflags、googletest 等）均构建成功，唯独 libaio 下载阶段失败。

## 修复方向

### 方向 1（置信度: 高）
修改 fix_getdeps.py 的补丁策略，不再仅跳过 `_verify_hash`，而是进一步修补 getdeps.py 的下载逻辑，使其在检测到下载目录中已存在同名文件时跳过实际下载。具体需要修补 `fetcher.py` 中的 `download` 方法，在发起 HTTP 请求前检查目标文件是否已存在且大小合理（> 0 字节），若存在则直接返回已存在的文件路径，避免覆盖预置的合法 tar.gz。

### 方向 2（置信度: 中）
在 Dockerfile 的 RUN 命令中，调整操作顺序：先运行 fix_getdeps.py 打补丁，再将本地 libaio.tar.gz 复制到下载目录（在 getdeps.py 创建下载目录之后）。同时确认预置文件名与 getdeps.py 构造的下载文件名完全一致（包括 `libaio-libaio-libaio-` 三重前缀）。

### 方向 3（置信度: 低）
将 libaio 的下载源从 `pagure.io` 更换为其他可用的镜像或归档站点（如 GitHub），在 fix_getdeps.py 或 getdeps 的 manifest 中修改 libaio 的下载 URL。此方向需要确认 libaio 在其他站点有对应的版本归档。

## 需要进一步确认的点
1. getdeps.py 中 `fetcher.py` 的 `download` 方法实际逻辑：确认其在什么条件下会跳过已有文件、什么条件下会覆盖。需查看 `build/fbcode_builder/getdeps/fetcher.py` 中 download 方法的实现细节。
2. libaio 在 pagure.io 上的实际状态：确认该 URL 是否永久失效（项目迁移/归档删除），或仅为临时性网络问题。
3. 是否 getdeps.py 的 manifest 中 hardcode 了 libaio 的下载 URL，如果是，是否可以在 fix_getdeps.py 中一并替换该 URL。
