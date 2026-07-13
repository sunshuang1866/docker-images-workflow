# CI 失败分析报告

## 基本信息
- PR: #3108 — chore(mesos): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式02
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [ 3/10] RUN wget https://www.openssl.org/source/old/1.0.2/openssl-1.0.2k.tar.gz ...
#9 0.162 --2026-07-13 08:15:08--  https://www.openssl.org/source/old/1.0.2/openssl-1.0.2k.tar.gz
#9 0.426 HTTP request sent, awaiting response... 301 Moved Permanently
#9 0.722 Location: https://github.com/openssl/openssl/releases/download/openssl-1.0.2k/openssl-1.0.2k.tar.gz [following]
#9 0.858 HTTP request sent, awaiting response... 404 Not Found
#9 1.184 2026-07-13 08:15:09 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://www.openssl.org/source/old/1.0.2/openssl-1.0.2k.tar.gz && ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/mesos/1.11.0/24.03-lts-sp4/Dockerfile:20-24`
- 失败原因: `https://www.openssl.org/source/old/1.0.2/openssl-1.0.2k.tar.gz` 返回 HTTP 301 重定向至 `https://github.com/openssl/openssl/releases/download/openssl-1.0.2k/openssl-1.0.2k.tar.gz`，该 GitHub Release 上的旧版本制品已不存在（404 Not Found），导致 wget 下载失败。

### 与 PR 变更的关联
PR 新增了 `Bigdata/mesos/1.11.0/24.03-lts-sp4/Dockerfile`，其中第 20 行硬编码了 `https://www.openssl.org/source/old/1.0.2/openssl-1.0.2k.tar.gz` 作为 OpenSSL 1.0.2k 的下载地址。该 URL 在上游已失效（openssl.org 将旧版本重定向到 GitHub Releases，而 GitHub 上的 release asset 已被移除），导致 `[ 3/10]` 构建步骤失败。此失败由 PR 代码直接触发。

## 修复方向

### 方向 1（置信度: 高）
将 OpenSSL 1.0.2k 的下载源切换为其他稳定的归档镜像源（如 `https://github.com/openssl/openssl/archive/refs/tags/OpenSSL_1_0_2k.tar.gz`，即 GitHub 的 自动生成的源码归档包，而非 Release 附件），或使用 OpenSSL 官方 FTP 归档（如 `ftp://ftp.openssl.org/source/old/1.0.2/openssl-1.0.2k.tar.gz`）。

### 方向 2（置信度: 中）
如果 openEuler 24.03-LTS-SP4 的 yum 仓库提供了兼容版本的 openssl 开发包，可以考虑用系统包管理器安装（如 `yum install -y openssl-devel`）替代从源码编译 OpenSSL 1.0.2k。但需要注意 Mesos 1.11.0 是否强制要求此特定版本的 OpenSSL。

## 需要进一步确认的点
1. 确认 `ftp.openssl.org` 或 `https://github.com/openssl/openssl/archive/refs/tags/OpenSSL_1_0_2k.tar.gz`（GitHub 源码归档）是否仍提供 OpenSSL 1.0.2k 源码包。
2. 确认 Mesos 1.11.0 能否接受其他 OpenSSL 1.0.2 小版本（如 1.0.2u）替代 1.0.2k。
3. 确认 openEuler 24.03-LTS-SP4 的默认 OpenSSL 版本（日志显示安装了 `openssl-1:3.5.6-4`）能否满足 Mesos 1.11.0 构建要求，如可则无需从源码编译 OpenSSL 1.0.2k。
4. 日志中还有两个 BuildKit 警告：
   - `UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH' (line 41)` — Dockerfile 第 41 行 `ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:...` 自引用未定义变量。
   - `LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 51)` — Dockerfile 第 51 行 `ENV PATH $PATH:/mesos/bin` 使用了旧式格式。
   虽然这些警告未直接导致构建失败，但建议一并修复。

## 修复验证要求
1. code-fixer 必须验证所选的替代下载源（GitHub archive tag 或 ftp.openssl.org）中确实存在 `openssl-1.0.2k.tar.gz` 文件，且 SHA256 校验和与 OpenSSL 官方公布的 `6dd94765d28b55e9554dee771796957154470372156d6d3c2382d5a6795a0c8f` 一致。
2. 如替换为系统 openssl-devel，需验证 Mesos 1.11.0 的 `./configure` 能正确检测并使用系统 OpenSSL。
3. 如替换为其他 OpenSSL 小版本（如 1.0.2u），需同步修改 Dockerfile 中对应目录名和 URL，并验证 Mesos 构建通过。
