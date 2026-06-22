# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨发行版RPM依赖冲突
- 新模式症状关键词: `Failed dependencies`, `libm.so.6(GLIBC_2.17)`, `foundationdb-clients`, `el9.aarch64`, `openEuler`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
------
Dockerfile:22
--------------------
  21 |     
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
  25 |     
--------------------
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB 仅发布面向 RHEL 7/8/9 的官方 RPM 制品，Dockerfile 硬编码下载了 `el9.aarch64` RPM。该 RPM 声明了对 `libm.so.6(GLIBC_2.17)(64bit)` 的依赖（RHEL glibc RPM 的 provides 元数据格式），但在 openEuler 24.03 中 glibc RPM 包未提供完全匹配的 RPM provides 元数据，导致 `rpm -ivh` 依赖解析失败。

### 与 PR 变更的关联
该 Dockerfile (`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`) 完全是本次 PR 新增的文件（+69 行），构建失败直接由 PR 引入。Dockerfile 在基础镜像 `openeuler/openeuler:24.03-lts-sp3` 中尝试安装 FoundationDB 的 RHEL 9 原生 RPM，两个发行版的 RPM 依赖元数据不兼容。

## 修复方向

### 方向 1（置信度: 高）
使用 `rpm -ivh --nodeps` 跳过 RPM 依赖检查，直接安装 FoundationDB 客户端二进制文件。原因是 `libm.so.6(GLIBC_2.17)` 对应的 glibc 符号在 openEuler 24.03 的 glibc 2.38 中实际存在（向后兼容至 GLIBC_2.0），仅为 RPM 元数据层面的差异而非运行时缺失。安装后需通过 `ldd` 验证 FDB 客户端二进制能正常链接。

### 方向 2（置信度: 中）
改用 FoundationDB 官方 Docker 镜像的多阶段构建（类似模式16），从 `foundationdb/foundationdb:7.3.77` 中 `COPY --from` 提取客户端二进制文件（`fdbcli`、`libfdb_c.so` 等），完全绕过 RPM 安装步骤。需确认官方镜像的 `fdbcli` 版本与 Dockerfile 中的 VERSION 一致。

### 方向 3（置信度: 低）
从 FoundationDB 源码构建客户端库（`fdbclient`、`fdb_c`），但这会增加构建复杂度和时间，且需要额外处理 cmake 依赖。

## 需要进一步确认的点
1. 确认 openEuler 24.03 基础镜像中 `libm.so.6` 实际提供的 GLIBC 符号版本范围（`readelf -V /lib64/libm.so.6 | grep GLIBC`），验证 `GLIBC_2.17` 符号确实存在于运行时库中。
2. 确认 FoundationDB 7.3.77 客户端二进制在 openEuler 24.03 上使用 `--nodeps` 安装后能否正常链接和运行（`ldd /usr/bin/fdbcli`）。
3. 日志中后续步骤 `git clone --depth 1` + `git checkout ${VERSION} 2>/dev/null || true` 存在模式18描述的浅克隆与 commit hash checkout 不兼容问题（被 `|| true` 掩盖），修复当前 RPM 问题后可能暴露此后续问题，需一并关注。

## 修复验证要求
若采用方向1（`--nodeps`），code-fixer 必须在提交前验证：
- 在 `openeuler/openeuler:24.03-lts-sp3` 容器中执行 `rpm -ivh --nodeps fdb-clients.rpm` 后，运行 `ldd /usr/bin/fdbcli` 确认无未解析符号。
- 运行 `/usr/bin/fdbcli --version` 确认输出 `FoundationDB CLI 7.3` 且无段错误。
