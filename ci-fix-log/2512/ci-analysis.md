# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM 架构不匹配
- 新模式症状关键词: error: Failed dependencies, libm.so.6, GLIBC, needed by, aarch64, foundationdb-clients

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL ... rpm -ivh ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中硬编码了 FoundationDB 的 aarch64 RPM 下载地址 (`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`)，但当前 CI 构建环境为 x86_64（证据：步骤 #8 rustup 输出 `default host triple is x86_64-unknown-linux-gnu`，步骤 #9 meson 输出 `Host machine cpu family: x86_64`）。在 x86_64 目标平台上安装 aarch64 架构的 RPM 包时，RPM 依赖解析器无法在 x86_64 glibc 的 provides 中找到 aarch64 二进制所需的 `libm.so.6(GLIBC_2.17)(64bit)`。

### 与 PR 变更的关联
PR #2512 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（+69 行），其中第 22-24 行的 FoundationDB RPM 安装步骤硬编码了 aarch64 架构的 RPM URL。该 Dockerfile 在本次 PR 中首次引入，失败由 PR 直接触发。

## 修复方向

### 方向 1（置信度: 高）
使用 BuildKit 内置变量 `TARGETARCH` 或 Shell 命令 `$(uname -m)` 动态选择正确的 RPM 架构。FoundationDB 在 GitHub Releases 上同时提供 `x86_64` 和 `aarch64` 架构的 RPM 包，URL 模式为 `foundationdb-clients-{VERSION}-1.el9.{arch}.rpm`，需要根据目标架构替换 `aarch64` 为对应值。

### 方向 2（置信度: 中）
如果 FoundationDB 7.3.77 没有提供 x86_64 RPM（上游可能仅发布 aarch64），则需改用 FoundationDB 官方 Docker 镜像的多阶段构建方式（`COPY --from=foundationdb/foundationdb:7.3.77`），或直接从 FoundationDB 源码编译客户端库。

## 需要进一步确认的点
1. 确认 FoundationDB 7.3.77 在 GitHub Releases 上是否提供 x86_64 RPM 包（URL: `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`）
2. 确认 openEuler 24.03 的 glibc 是否实际提供了 `libm.so.6(GLIBC_2.17)` 符号（即使架构匹配，EL9 RPM 对 openEuler 的兼容性也需验证）
3. 历史模式 18 提及本 PR 的 `--depth 1` + commit hash checkout 问题——当前日志中基金会DB 步骤先失败，因此 git clone 步骤（步骤 6/9）未执行到。若修复 RPM 问题后构建推进，需注意 git clone 浅克隆与 commit hash 的兼容性问题
