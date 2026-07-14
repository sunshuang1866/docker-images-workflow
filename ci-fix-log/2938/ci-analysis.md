# CI 失败分析报告

## 基本信息
- PR: #2938 — chore(wireshark): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式02
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#8 [3/5] RUN wget https://www.wireshark.org/download/src/wireshark-4.6.5.tar.xz ...
#8 0.135 --2026-07-09 13:14:57--  https://www.wireshark.org/download/src/wireshark-4.6.5.tar.xz
#8 0.164 Resolving www.wireshark.org (www.wireshark.org)... 172.67.75.39, 104.26.10.240, 104.26.11.240, ...
#8 0.165 Connecting to www.wireshark.org (www.wireshark.org)|172.67.75.39|:443... connected.
#8 0.250 HTTP request sent, awaiting response... 404 Not Found
#8 1.719 2026-07-09 13:14:58 ERROR 404: Not Found.
```

### 根因定位
- 失败位置: `Others/wireshark/4.6.5/24.03-lts-sp4/Dockerfile:13`（wget 下载步骤）
- 失败原因: Dockerfile 中硬编码的下载 URL `https://www.wireshark.org/download/src/wireshark-${VERSION}.tar.xz`（展开为 `wireshark-4.6.5.tar.xz`）返回 HTTP 404。Wireshark 4.6.5 不再是上游最新版本，源码包已从主下载目录下架。Wireshark 官方将非最新版本的源码归档到 `all-versions` 子目录（`https://www.wireshark.org/download/src/all-versions/`），而 Dockerfile 使用了主下载路径。

### 与 PR 变更的关联
直接关联。PR #2938 新增了 `Others/wireshark/4.6.5/24.03-lts-sp4/Dockerfile`，该文件中的 wget URL 指向了 Wireshark 上游已下架的主下载路径，导致 Docker 构建在第 8 层（下载步骤）失败。这是新增 Dockerfile 引入的问题，不是项目已有的系统性问题。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 第 13 行的下载 URL 从主路径改为归档路径：
- 当前: `https://www.wireshark.org/download/src/wireshark-${VERSION}.tar.xz`
- 修改为: `https://www.wireshark.org/download/src/all-versions/wireshark-${VERSION}.tar.xz`

Wireshark 官方将所有非最新版本的 tar.xz 包保留在 `all-versions` 子目录下，该路径可稳定访问历史版本。

### 方向 2（置信度: 高）
使用 `https://2.na.dl.wireshark.org/src/all-versions/wireshark-${VERSION}.tar.xz` 作为备用下载源（Wireshark 官方 CDN）。

## 需要进一步确认的点
- 确认同目录下的 SP3 Dockerfile（`Others/wireshark/4.6.5/24.03-lts-sp3/Dockerfile`）是否使用了同一 URL，如果 SP3 仍然通过 CI，可能是 SP3 的构建时间早于 Wireshark 下架 4.6.5 的时间，或者在 SP3 Dockerfile 中已经使用了 `all-versions` 路径。建议对照查看 SP3 Dockerfile 的下载 URL 以确认差异。
