# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB clients RPM 下载 URL 硬编码 `aarch64` 架构，导致在 x86_64 CI 构建机上 `rpm -ivh` 失败（依赖 `libm.so.6(GLIBC_2.17)(64bit)` 无法满足）。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 移除 FoundationDB RPM 安装流程（含硬编码架构的 URL），改用多阶段构建从 `foundationdb/foundationdb` 官方镜像 COPY 二进制文件 + 独立下载 headers tar.gz。

## 修复逻辑
已通过多个提交完成修复（`f5e9729e` → `0e0615db` → `beb06627` → `4f26bf3b`），最终方案：

1. **第 2-4 行**：声明 `ARG FDB_VERSION=7.3.77` 并添加 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 作为第一个构建阶段，利用 Docker 多架构镜像自动匹配构建平台架构。
2. **第 26-27 行**：用 `COPY --from=fdb` 从该阶段复制 `fdbcli` 和 `libfdb_c.so`，替代原有的 RPM 下载+安装步骤。此方案完全避免架构硬编码问题，因为 Docker 会根据构建平台自动拉取对应架构的 `foundationdb/foundationdb` 镜像。
3. **第 29-32 行**：独立下载 `fdb-headers-${FDB_VERSION}.tar.gz`（已从上游 7.3.77 验证 URL 有效，返回有效 gzip 内容），headers 为架构无关文件。

此修复对应分析报告中的**修复方向 1（置信度: 高）**——将架构硬编码替换为自适应方案。COPY 方式天然自适应架构，优于在 URL 中拼接 `${ARCH}` 变量的方案。

## 潜在风险
- `foundationdb/foundationdb:7.3.77` 镜像托管在 Docker Hub，构建时需确保网络可访问该 registry。
- `fdb-headers-7.3.77.tar.gz` 从 GitHub Releases 下载，依赖 GitHub 可用性。
- 若 `foundationdb/foundationdb` 镜像未来版本中内部文件路径变更，COPY 指令可能失败，但当前 7.3.77 版本路径稳定。