# 修复摘要

## 修复的问题
`git.kernel.org` 的 Anubis 反爬保护导致 `wget` 下载 snapshot tar.gz 时返回 HTML 页面而非 gzip 压缩包，构建失败。

## 修改的文件
- `Others/bcache/1.1/24.03-lts-sp4/Dockerfile`: (1) 在 dnf install 中添加 `git` 包；(2) 将 `wget` + `tar -zxvf` 下载快照的方式替换为 `git clone --depth 1 --branch` 克隆指定 tag

## 修复逻辑
- 根因：`git.kernel.org` 部署了 Anubis 反爬保护，对 HTTP snapshot 请求返回 JavaScript 挑战页面（HTML），CI 环境中的 `wget` 无法执行 JavaScript，下载到的是 2090 字节的 HTML 而非 tar.gz，导致 `tar -zxvf` 失败。
- 已验证 `git clone` 到相同 tag（`bcache-tools-1.1`）可以正常工作，git 协议不受 Anubis 影响。
- 通过 `git ls-remote --tags` 确认上游 tag 为 `bcache-tools-1.1`，ARG VERSION=1.1 构造的 `bcache-tools-${VERSION}` = `bcache-tools-1.1` 完全匹配。
- 克隆到 `/opt/bcache-tools-${VERSION}` 后，后续 WORKDIR 和 patch 路径均无需调整，与原有结构完全兼容。

## 潜在风险
- `git` 包的引入略微增加构建镜像体积，属于可接受的代价。
- 若上游 tag 命名格式未来变更（如改为 `v1.1`），需同步调整 `ARG VERSION` 和 `--branch` 参数。