# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构，导致 x86_64 CI 构建失败。该问题已通过先前的多次修复提交解决，当前代码无需额外修改。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 已由先前的修复提交（`beb06627`, `0eed6b50`, `4f26bf3b`）将硬编码 aarch64 RPM 下载方案替换为多阶段构建方案（`FROM foundationdb/foundationdb` + `COPY --from=fdb`），该方案与架构无关。

## 修复逻辑
CI 分析报告指出的根因是 Dockerfile 中 FoundationDB 客户端 RPM 的 URL 硬编码为 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`，在 x86_64 构建环境上无法安装。修复分支（`fix/2512`）上已通过以下提交序列解决了此问题：

1. `beb06627`: 移除了 `curl + rpm -i` 的架构特定 RPM 下载方式，改为多阶段构建 — 从 `foundationdb/foundationdb:7.3.77`（官方镜像，支持 `amd64` 和 `arm64` 两种架构）复制 `fdbcli` 与 `libfdb_c.so`
2. `4f26bf3b`: 新增 FDB 头文件下载（架构无关），供 3FS 编译时链接使用

当前方案使用 Docker 多阶段构建 + `COPY --from=fdb`，Docker 会自动为每个目标平台拉取对应架构的镜像变体，完全消除了架构硬编码问题。已验证 `foundationdb/foundationdb:7.3.77` 在 Docker Hub 上同时提供 `amd64` 和 `arm64` 镜像，`COPY` 路径（`/usr/bin/fdbcli`, `/usr/lib/libfdb_c.so`）与上游 FoundationDB Dockerfile 中的实际路径一致。

## 潜在风险
- 多阶段构建方案依赖 `foundationdb/foundationdb:7.3.77` 镜像持续可用；若该镜像被归档或下线，需恢复为架构感知的 RPM 下载方案
- 若 3FS 将来需要特定于分发包的 FoundationDB 客户端文件路径（如 `/etc/foundationdb`），多阶段构建方案可能不完整，需额外处理