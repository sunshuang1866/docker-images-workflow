# 修复摘要

## 修复的问题
FoundationDB 客户端 RPM (`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`) 在 openEuler 24.03 上通过 `rpm -ivh` 安装时因跨发行版依赖不兼容失败（`libm.so.6(GLIBC_2.17)(64bit) is needed`）。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将硬编码下载 EL9 RPM 并执行 `rpm -ivh` 的安装方式，替换为多阶段构建从 FoundationDB 官方 Docker 镜像 (`foundationdb/foundationdb:7.3.77`) 中直接复制客户端二进制文件。

## 修复逻辑
CI 分析报告指出根因是 EL9/RHEL 9 构建的 FoundationDB RPM 在 openEuler 24.03 基础镜像上存在 glibc 符号版本兼容性问题（RPM 依赖解析器无法识别 `GLIBC_2.17` 符号已满足）。推荐修复方案（置信度: 高）是改为多阶段构建，从 FoundationDB 官方 Docker 镜像中提取客户端二进制，规避跨发行版 RPM 依赖冲突。

已验证：
1. `foundationdb/foundationdb:7.3.77` 在 Docker Hub 存在，支持 `linux/amd64` 和 `linux/arm64`
2. 已从上游 `release-7.3` 分支获取 FoundationDB Dockerfile 验证，客户端二进制路径 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 与 COPY 指令完全匹配
3. FoundationDB headers tarball (`fdb-headers-7.3.77.tar.gz`) 在 GitHub Releases 中可正常下载

具体改动：移除 `RUN curl ... rpm ... rpm -ivh /tmp/fdb-clients.rpm` 行，新增：
- `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 声明多阶段构建
- `COPY --from=fdb /usr/bin/fdbcli /usr/bin/fdbcli`
- `COPY --from=fdb /usr/lib/libfdb_c.so /usr/lib64/libfdb_c.so`
- 新增 header 文件的 tarball 下载

## 潜在风险
- FoundationDB 二进制本身仍基于 EL9 编译，运行时动态链接可能依赖特定 glibc 符号版本。若 openEuler 24.03 的 glibc 实际包含了所需符号（仅 RPM 元数据未声明），则运行时无问题；若符号缺失，运行时可能出现动态链接错误。CI 分析报告建议后续在运行容器中执行 `ldd` 验证。
- 3FS 源码编译步骤（第 11 步）因原第 10 步失败从未执行过，修复后可能暴露新的编译错误，但该风险不在本次 CI 失败分析范围内。