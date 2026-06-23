# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构/发行版不兼容
- 新模式症状关键词: Failed dependencies, libm.so.6(GLIBC, foundationdb, el9, aarch64, rpm -ivh

## 根因分析

### 直接错误
```
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中硬编码了 `aarch64` 架构的 FoundationDB RPM 下载 URL，但实际构建环境为 x86_64（日志中 Rust 报告 `x86_64-unknown-linux-gnu`、Meson 报告 `Host machine cpu family: x86_64`）。此外，该 RPM 是为 RHEL/CentOS 9（`el9`）构建的，其依赖 `libm.so.6(GLIBC_2.17)(64bit)` 的 RPM 依赖声明与 openEuler 的 glibc 打包方式不兼容，导致 `rpm -ivh` 依赖检查失败。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，该 Dockerfile 第 22-24 行使用了硬编码的架构和发行版特定的 FoundationDB RPM URL，直接触发了本次构建失败。即使修正架构字符串（如改为 `x86_64`），RPM 的 glibc 版本化符号依赖仍可能在 openEuler 上不满足，需要额外处理。

## 修复方向

### 方向 1（置信度: 高）
**使用 BuildKit 变量动态选择架构 + 绕过 RPM 依赖检查**  
1. 将 RPM URL 中的 `aarch64` 替换为 `$(case $(uname -m) in x86_64) echo amd64;; aarch64) echo aarch64;; esac)` 以动态选择正确架构的 RPM。  
2. 将 `rpm -ivh` 替换为 `rpm -ivh --nodeps` 以绕过 openEuler 与 EL9 之间的 RPM 依赖差异，或改用 `rpm2cpio | cpio -idmv` 手动提取 FoundationDB 客户端二进制文件到系统路径。

### 方向 2（置信度: 中）
**放弃 RPM 安装，改用 FoundationDB 客户端二进制包或从源码编译**  
如果 FoundationDB 也提供 `.tar.gz` 格式的客户端包，可直接下载解压并将二进制和库文件放到 `/usr/local/bin` 和 `/usr/local/lib`，完全避开 RPM 依赖问题。若仅有 `.deb` 包，可考虑用 `alien` 转换（但需要先安装 alien）。

## 需要进一步确认的点
1. FoundationDB 7.3.77 是否提供 x86_64/amd64 架构的 RPM 或 tar.gz 客户端包？需检查 `https://github.com/apple/foundationdb/releases/tag/7.3.77` 的实际发布资产列表。
2. openEuler 24.03-LTS-SP3 上 `libm.so.6` 提供的 GLIBC 版本符号版本号是什么？可进入 openEuler 容器执行 `readelf -s /lib64/libm.so.6 | grep GLIBC` 确认。
3. 3FS 是否严格要求 FoundationDB 7.3.77，还是可以使用其他版本？3FS 文档中对 FoundationDB 版本的兼容性要求需确认。
4. 修复 RPM 依赖问题后，需确认后续构建步骤（如 `git clone --depth 1` + commit hash checkout，见知识库模式 18）是否也会失败。

## 修复验证要求
1. code-fixer 必须进入 `openeuler/openeuler:24.03-lts-sp3` 容器，手动执行 `readelf -s /lib64/libm.so.6 | grep GLIBC` 确认 openEuler 实际提供的 glibc 符号版本，验证 `--nodeps` 方案后 FoundationDB 客户端二进制能否正常运行。
2. code-fixer 必须确认 FoundationDB 7.3.77 的 GitHub Release 页面实际提供哪些架构的 RPM/包，验证替换架构后的 URL 可下载。
3. 修复后必须在 openEuler 24.03-lts-sp3 容器内完整验证 `rpm -ivh` 及 FoundationDB 客户端（`fdbcli`）可正常启动。
