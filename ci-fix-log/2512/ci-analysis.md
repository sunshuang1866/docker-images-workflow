# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨发行版 RPM 依赖不兼容
- 新模式症状关键词: error: Failed dependencies, libm.so.6, GLIBC_2.17, foundationdb-clients, aarch64, el9, rpm -ivh

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`:22-24
- 失败原因: Dockerfile 中硬编码下载 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`（面向 RHEL 9 / aarch64 的 RPM 包），该 RPM 声明的 `libm.so.6(GLIBC_2.17)` 版本化依赖在 openEuler 24.03 的 glibc 中无法解析（glibc 符号版本提供方式不兼容）。此外，构建环境实际为 x86_64 架构（rustup 检测到 `x86_64-unknown-linux-gnu`，meson 检测到 `cpu family: x86_64`），而 RPM 硬编码为 aarch64，即便依赖解决也存在架构不匹配的二次风险。

### 与 PR 变更的关联
PR 新增了完整的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行），其中的第 22-24 行硬编码了 FoundationDB RPM 下载和安装命令。该 RPM 是为 RHEL 9 aarch64 构建的，与 openEuler 基础镜像的 glibc 版本和实际构建架构不兼容，属于 PR 引入的全新构建错误。

**注意**: 日志中步骤 #7（yum 安装）、#8（Rust 安装）、#9（FUSE 编译）均成功完成，步骤 #10 才失败。后续 git clone + cmake 构建步骤（步骤 #6/9）尚未执行到——该步骤中已知存在 `--depth 1` + commit hash checkout 兼容性问题（见历史模式 18），但本次 CI 失败先触发于 FDB RPM 安装阶段。

## 修复方向

### 方向 1（置信度: 高）
FoundationDB clients RPM 是为 RHEL 9 aarch64 构建的，而 openEuler 使用不同版本的 glibc。应考虑以下替代方案之一：
1. **从 FoundationDB 官方 Docker 镜像提取二进制**：采用多阶段构建（`FROM foundationdb/foundationdb:7.3.77 AS fdb-source`），然后 `COPY --from=fdb-source /usr/bin/fdbcli /usr/lib/libfdb_c.so ...` 到 openEuler 镜像中，绕过 RPM 依赖冲突。
2. **使用 FoundationDB 提供的 `.tar.gz` 归档包**（如存在），而非 `.el9` 系 RPM。
3. **从 FoundationDB 源码编译** fdb clients 库，使其链接 openEuler 的 glibc——但这会显著增加构建复杂度。

### 方向 2（置信度: 中）
如果 FoundationDB 提供面向通用 Linux（非特定发行版）的 `.rpm` 或 `.deb` 包，可替换 URL。需在 FoundationDB 7.3.77 GitHub Release 页面确认是否有 `foundationdb-clients-7.3.77-1.x86_64.rpm` 或 `foundationdb-clients_7.3.77-1_amd64.deb` 等可用制品。

## 需要进一步确认的点
1. FoundationDB 7.3.77 Release 页面（`https://github.com/apple/foundationdb/releases/tag/7.3.77`）上是否提供了 x86_64 架构的 RPM 或 tar.gz 包？若有 x86_64 RPM，其在 openEuler 上的依赖解析情况如何？
2. 若采用多阶段构建从 `foundationdb/foundationdb:7.3.77` 提取二进制，需确认该官方镜像中 `/usr/lib/libfdb_c.so` 及其头文件是否存在，且目标 ELF 依赖（`libm.so.6`、`libc++.so.1` 等）在 openEuler 上能否通过 `yum install` 满足。
3. 该 Dockerfile 后续步骤（git clone + cmake 构建）中已知的 `--depth 1` + commit hash checkout 问题（模式 18）在当前 CI 运行中尚未触发，但修复 FDB 安装后必然暴露，需一并处理。

## 修复验证要求
若修复方向涉及从 FoundationDB Release 页面更换 URL 或切换到 tar.gz 归档：
- code-fixer 必须实际访问 `https://github.com/apple/foundationdb/releases/tag/7.3.77` 确认目标文件存在且架构匹配。
- 若采用多阶段构建，必须在 openEuler 24.03-lts-sp3 容器中验证 `COPY --from` 提取的二进制文件能正常运行，且 3FS cmake 能找到 `libfdb_c.so`。
