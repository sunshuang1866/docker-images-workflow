# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 预置文件命名不匹配
- 新模式症状关键词: download, pagure.io, text/html, Content-Type, tar.gz, filename mismatch, getdeps, libaio

## 根因分析

### 直接错误
```
#11 340.9 Assessing libaio...
#11 340.9 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> .../downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 340.9 Date: Tue, 09 Jun 2026 13:11:41 GMT
#11 340.9 Server: Apache/2.4.37 (Red Hat Enterprise Linux) OpenSSL/1.1.1k mod_wsgi/4.6.4 Python/3.6
#11 340.9 Content-Type: text/html; charset=utf-8
...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} ... && ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/Dockerfile`:18 (RUN 命令中 `./build/fbcode_builder/getdeps.py` 调用)
- 失败原因: Dockerfile 中预置的 libaio tarball 文件名 `libaio-libaio-0.3.113.tar.gz` 与 getdeps 构建系统期望的下载文件名 `libaio-libaio-libaio-0.3.113.tar.gz` 不一致，导致 getdeps 未找到预置文件，转而从 pagure.io 网络下载，而 pagure.io 返回了 HTML 页面（Content-Type: text/html）而非有效的 tar.gz 归档，触发构建失败。

### 与 PR 变更的关联

PR 新增了 4 个文件以实现 fbthrift v2026.06.08.00 的容器镜像构建：

1. **Dockerfile** (`Others/fbthrift/2026.06.08.00/24.03-lts-sp3/Dockerfile`): 第 20 行 `cp /tmp/libaio.tar.gz .../downloads/libaio-libaio-0.3.113.tar.gz` 中，目标文件名缺少一个 `libaio-` 前缀。getdeps 在 `Assessing libaio` 时根据上游 manifest 生成的期望下载路径为 `.../downloads/libaio-libaio-libaio-0.3.113.tar.gz`（三前缀），而 Dockerfile 只提供了两前缀的文件名，造成文件名不匹配。

2. **fix_getdeps.py** (`Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`): 该脚本跳过 libaio 哈希校验（修改 `_verify_hash` 为空操作）是正确的思路，但它无法解决"文件未找到导致回退到网络下载"的问题。文件名不匹配发生在更上游——getdeps 在查找本地文件阶段就已跳过预置文件。

**结论：此失败由本次 PR 的变更直接引发。** Dockerfile 中预置 tarball 的目标文件名与 getdeps 期望的文件名不一致，是导致构建失败的直接原因。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 第 20 行的 `cp` 目标文件名从 `libaio-libaio-0.3.113.tar.gz` 改为 `libaio-libaio-libaio-0.3.113.tar.gz`，使其与 getdeps 构建系统根据上游 manifest（`build/fbcode_builder/manifests/libaio`）生成的期望下载文件名完全一致。

### 方向 2（置信度: 低）
若方向 1 仍失败（即 getdeps 仍尝试从 pagure.io 下载），可进一步考虑在 `fix_getdeps.py` 中增加对 getdeps fetcher 的修改，使其在本地文件存在时直接跳过下载步骤，而非仅跳过哈希校验。

## 需要进一步确认的点
1. 确认 getdeps 上游 manifest（`build/fbcode_builder/manifests/libaio`）中 libaio 的下载 URL 是否确实为 `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz`，以及该 manifest 生成的本地缓存文件名格式是否为 `libaio-libaio-libaio-0.3.113.tar.gz`。
2. 确认 `pagure.io` 对 fbthrift 仓库 libaio 版本的归档 URL 是否可用——从日志看服务器返回了 HTML 而非 tar.gz，可能该归档在 pagure.io 上已失效，需确认是否需要更换 libaio 下载源或改用其他镜像。
