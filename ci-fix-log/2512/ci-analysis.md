# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨架构RPM硬编码
- 新模式症状关键词: error: Failed dependencies, libm.so.6(GLIBC_2.17), aarch64, el9, foundationdb-clients

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB 客户端的 RPM 下载 URL 硬编码了 `aarch64` 架构和 `el9` 发行版标识，而当前 CI 构建环境为 `x86_64`（rust 安装器输出 `default host triple is x86_64-unknown-linux-gnu`）。该 RPM 是为 RHEL/CentOS 9 aarch64 构建的，与 openEuler x86_64 环境存在双重不兼容：① 架构不匹配（aarch64 RPM 无法安装在 x86_64 上）；② 发行版不兼容（el9 RPM 依赖的 `libm.so.6(GLIBC_2.17)` 版本符号在 openEuler 中不可用）。

### 与 PR 变更的关联
PR 新增了整个 `Storage/3fs/` 目录，其中 `Dockerfile:22-24` 的 FoundationDB RPM 安装步骤是全新的。该错误由 PR 变更直接引入：Dockerfile 未使用 BuildKit 的 `TARGETARCH` 动态选择对应架构的 RPM，也未使用 `--force` 或 `--nodeps` 绕过发行版依赖检查。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB 客户端的安装方式从"直接下载 el9 aarch64 RPM"改为根据目标架构动态选择：
- 使用 BuildKit 内置变量 `TARGETARCH`（`amd64`/`arm64`）映射为 FoundationDB 官方发布的不同架构 RPM 文件名
- 对于 `amd64`（x86_64）下载 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`
- 对于 `arm64`（aarch64）下载 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`
- 若 `libm.so.6(GLIBC_2.17)` 依赖在 openEuler 上确实无法满足，可尝试 `rpm -ivh --nodeps` 绕过（但需验证运行时 FoundationDB 客户端库能否正常工作），或改用官方 tar.gz 二进制分发包替代 RPM

### 方向 2（置信度: 中）
从 FoundationDB 官方 Docker 镜像（`foundationdb/foundationdb:7.3.77`）中 `COPY --from` 提取客户端库二进制文件，完全绕过 RPM 依赖问题。这种方式对 openEuler 的兼容性最好。

### 方向 3（置信度: 低，备选）
检查 openEuler 的 EPOL 或官方仓库是否提供了 `foundationdb-clients` 包，如果有则直接 `yum install -y foundationdb-clients`，无需从外部下载 RPM。

## 需要进一步确认的点
1. FoundationDB 7.3.77 的 `el9.x86_64.rpm` 在 openEuler 24.03-lts-sp3 x86_64 容器中是否同样存在 `libm.so.6(GLIBC_2.17)` 依赖问题（即该问题是否仅影响 aarch64 架构，还是两个架构都有）
2. openEuler 24.03-lts-sp3 的 glibc 版本及提供的 `GLIBC_2.17` 符号版本是否存在
3. 使用 `rpm -ivh --nodeps` 安装后，FoundationDB C 客户端库（`libfdb_c.so`）在 openEuler 上能否正常链接和工作
4. FoundationDB 官方是否提供了独立于发行版的纯二进制 tar.gz 分发包（非 RPM 包装），如果有则是最安全的选择

## 修复验证要求
修复方案实施后，code-fixer 必须在 **x86_64 和 aarch64 两个架构的 openEuler 24.03-lts-sp3 容器**中分别验证：
1. FoundationDB 客户端 RPM（或替代安装方式）能否成功安装
2. `ldconfig -p | grep libfdb_c` 确认 `libfdb_c.so` 已正确注册
3. 3FS 的 cmake 构建能否找到 FoundationDB 客户端库并完成链接
