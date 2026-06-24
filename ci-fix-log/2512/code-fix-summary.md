# 修复摘要

## 修复的问题
FoundationDB RPM 跨架构安装失败：Dockerfile 中硬编码 `el9.aarch64` RPM URL，在 x86_64 CI 构建中因架构不匹配导致 `rpm -ivh` 依赖解析失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`：以多阶段构建 `COPY --from=fdb` 替代 RPM 安装步骤，修复了跨架构兼容性问题，同时移除了 `--depth 1` 浅克隆和 `boost-foundation` 错误包名。

## 修复逻辑
CI 分析报告（根因：RPM 跨发行版架构不匹配）指向 `Dockerfile:22` 的 `rpm -ivh` 步骤。修复通过多阶段构建从官方 `foundationdb/foundationdb:7.3.77` 镜像（已验证支持 linux/amd64 + linux/arm64 多架构）中 `COPY` 所需二进制文件，完全绕过 RPM 安装路径。同时：
- 移除了 git clone 的 `--depth 1` 参数以避免浅克隆与特定 commit checkout 的不兼容；
- 将 `boost-foundation` 更正为 `boost-filesystem boost-system boost-program-options`；
- 通过 tar.gz 下载架构无关的 FoundationDB headers。

已从上游 GitHub Release `7.3.77` 获取 `fdb-headers-7.3.77.tar.gz` 验证存在；Docker Hub 确认 `foundationdb/foundationdb:7.3.77` 提供 amd64 和 arm64 双架构镜像。

## 潜在风险
无。修复方案已通过多次迭代验证，当前 Dockerfile 在所有 CI 架构上均可正确构建。