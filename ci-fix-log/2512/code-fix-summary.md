# 修复摘要

## 修复的问题
将 FoundationDB 客户端的安装方式从硬编码 `aarch64`/`el9` 架构的 RPM 直接下载改为通过 `COPY --from=fdb` 从官方 FoundationDB Docker 镜像提取二进制文件，消除跨架构构建不兼容问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`:
  1. 新增 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 作为前置构建阶段（第 4 行）
  2. 新增 `ARG FDB_VERSION=7.3.77` 全局参数及构建阶段参数（第 2、9 行）
  3. 用 `COPY --from=fdb /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so` 替换原有的 RPM 下载安装逻辑（第 26-27 行，原为 `rpm -i --nodeps --noscripts /tmp/fdb-clients.rpm`）
  4. 添加 fdb-headers 下载步骤，从 GitHub Release 获取头文件（第 29-32 行）
  5. 其他配套调整：`yum install` 中添加 `libevent-devel`，`git clone` 移除 `--depth 1` 选项，`yum install` 运行时库修正包名

## 修复逻辑
CI 失败分析报告中指出原始 Dockerfile 在安装 FoundationDB 客户端时硬编码了 `aarch64` 架构和 `el9` 发行版的 RPM URL，导致在 x86_64 的 CI 构建环境中因架构不匹配和 `libm.so.6(GLIBC_2.17)` 依赖缺失而失败。

修复采用分析报告中的"方向 2"方案：利用 FoundationDB 官方 Docker 镜像（`foundationdb/foundationdb:7.3.77`）作为前置构建阶段，通过 `COPY --from=fdb` 提取 `fdbcli` 和 `libfdb_c.so`。Docker 在构建时会根据目标平台自动拉取对应架构的镜像，从而彻底消除架构硬编码问题。同时，运行时已通过 `RUN ldconfig`（隐含在 yum 安装流程中）将 `libfdb_c.so` 注册到系统库路径。

已验证：从上游 `7.3.77` tag 获取 `fdb-headers-7.3.77.tar.gz` 头文件包下载 URL 有效。

## 潜在风险
- FoundationDB 客户端库（`libfdb_c.so`）来自 FoundationDB 官方 Docker 镜像，其编译时链接的 glibc 版本可能与 openEuler 24.03-lts-sp3 的 glibc 存在差异。若运行时出现符号未找到错误，需验证两个发行版的 glibc 版本兼容性。
- 无。