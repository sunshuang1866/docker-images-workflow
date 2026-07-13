# CI 失败分析报告

## 基本信息
- PR: #2929 — chore(bcache): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Git快照返回HTML
- 新模式症状关键词: `gzip: stdin: not in gzip format`, `text/html`, `saved [2090]`, `git.kernel.org`, `snapshot`

## 根因分析

### 直接错误
```
#11 [5/7] RUN wget https://git.kernel.org/pub/scm/linux/kernel/git/colyli/bcache-tools.git/snapshot/bcache-tools-1.1.tar.gz \
    && tar -zxvf bcache-tools-1.1.tar.gz \
    && rm -f bcache-tools-1.1.tar.gz
#11 0.056 --2026-07-10 09:07:28--  https://git.kernel.org/pub/scm/linux/kernel/git/colyli/bcache-tools.git/snapshot/bcache-tools-1.1.tar.gz
#11 0.666 HTTP request sent, awaiting response... 200 OK
#11 0.668 Length: unspecified [text/html]
#11 0.668 2026-07-10 09:07:28 (146 MB/s) - 'bcache-tools-1.1.tar.gz' saved [2090]
#11 0.670 gzip: stdin: not in gzip format
#11 0.670 tar: Child returned status 1
#11 0.670 tar: Error is not recoverable: exiting now
#11 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `Others/bcache/1.1/24.03-lts-sp4/Dockerfile:20`（wget + tar 步骤）
- 失败原因: `wget` 请求 `git.kernel.org` 的 snapshot URL（`bcache-tools-1.1.tar.gz`），服务器返回 `text/html` 内容（仅 2090 字节的 HTML 页面）而非 gzip 压缩包，`tar -zxvf` 解压时报 `not in gzip format`。

### 与 PR 变更的关联
**强关联**。本 PR 新增了 `Others/bcache/1.1/24.03-lts-sp4/Dockerfile`（31 行全新文件）和配套的 patch 文件。Dockerfile 中 `ARG VERSION=1.1` 构造的 snapshot URL `bcache-tools-${VERSION}.tar.gz`（即 `bcache-tools-1.1.tar.gz`）在 `git.kernel.org` 上不返回有效的 tar.gz 归档，直接导致构建失败。

可能的具体原因（按概率排序）:
1. **Tag 命名不匹配**：`git.kernel.org` 上 `colyli/bcache-tools.git` 仓库中的版本 tag 可能是 `v1.1`（带 `v` 前缀），而 URL 中使用的是裸版本号 `1.1`，导致 cgit 生成的快照文件名与请求不匹配，返回 HTML 页面而非归档。
2. **仓库路径或命名变更**：上游仓库 `colyli/bcache-tools.git` 的目录结构或 tag 命名规则已变更。
3. **SP1 版本也未使用该 URL**：现有的 `1.1/24.03-lts-sp1/Dockerfile` 可能使用了不同的下载源或不同的版本号格式，本 PR 的 Dockerfile 未正确对齐。

## 修复方向

### 方向 1（置信度: 中）
检查上游仓库 `git.kernel.org/pub/scm/linux/kernel/git/colyli/bcache-tools.git` 的实际 tag 列表，确认 tag 名称是否为 `v1.1`（带 `v` 前缀）。如果是，需修改 Dockerfile 中 `ARG VERSION=1.1` 为 `ARG VERSION=v1.1`，并同步调整 `WORKDIR /opt/bcache-tools-${VERSION}` 路径。

### 方向 2（置信度: 低）
若 tag 名称确认是 `1.1` 无误，说明 `git.kernel.org` 的 cgit 快照服务行为已变更（不直接返回归档）。可参考现有 SP1 版本的 Dockerfile（`1.1/24.03-lts-sp1/Dockerfile`）使用的下载方式，保持一致。

## 需要进一步确认的点
1. 确认 `git.kernel.org/pub/scm/linux/kernel/git/colyli/bcache-tools.git` 的 tag 列表，版本 1.1 对应的 tag 名称究竟是 `1.1` 还是 `v1.1`。
2. 查阅现有的 `Others/bcache/1.1/24.03-lts-sp1/Dockerfile`，确认其使用的下载 URL 是否与本 PR 新增的 Dockerfile 一致。如果 SP1 使用不同 URL 或不同方式且构建成功，应以此为准对齐。
3. 确认 kernel.org cgit 的 snapshot 功能是否对裸数字 tag（无 `v` 前缀）返回的是 HTML 列表页而非压缩包（cgit 已知行为：若 ref 不存在，返回仓库文件列表 HTML 页）。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（本次不涉及 patch 外部源文件，无需填写。）
