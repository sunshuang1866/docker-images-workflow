# 修复摘要

## 修复的问题
bzip2 预下载步骤使用了 sourceware.org 原始 URL，该 URL 返回 HTTP 403 Forbidden，导致 Docker 构建失败。

## 修改的文件
- `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`: 将第 45 行 curl 预下载 bzip2 的 URL 从 `https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz` 替换为 `https://distfiles.macports.org/bzip2/bzip2-1.0.8.tar.gz`，与同文件中 conan hook（第 33 行）使用的镜像保持一致。

## 修复逻辑
CI 分析报告指出：Dockerfile 中 conan hook（step #12）已将 bzip2 的 conandata.yml 中的 URL 替换为 `distfiles.macports.org` 镜像，但预下载 RUN 步骤（step #13）仍使用原始的 `sourceware.org` URL，导致该步骤自身因 403 而失败。修复采用分析报告推荐的方向 1（置信度: 高），将预下载步骤的 URL 改为镜像 URL。已验证 `https://distfiles.macports.org/bzip2/bzip2-1.0.8.tar.gz` 在当前网络环境中可达（HTTP 200），文件为有效 gzip（content-type: application/x-gzip）。

## 潜在风险
无。conan hook 中的匹配和替换逻辑保持不变（仍使用 sourceware.org 作为匹配源），预下载步骤直接使用镜像 URL，两者互不干扰。