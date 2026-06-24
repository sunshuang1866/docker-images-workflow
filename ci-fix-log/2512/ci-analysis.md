# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式 (与模式09、模式18、模式10 部分相关但根因不同)
- 新模式标题: RPM 架构硬编码
- 新模式症状关键词: Failed dependencies, aarch64, x86_64, rpm -ivh, foundationdb-clients, libm.so.6(GLIBC_2.17)

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm \
  https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
------
Dockerfile:22
ERROR: failed to solve: process "/bin/sh -c curl -sL ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`（PR 新增文件）
- 失败原因: Dockerfile 将 FoundationDB RPM 下载 URL 硬编码为 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），而当前 CI 构建运行在 `x86_64` 架构上（日志中 meson 输出 `Host machine cpu: x86_64`、rustup 输出 `default host triple is x86_64-unknown-linux-gnu` 可证）。x86_64 系统无法满足 aarch64 RPM 的 `libm.so.6(GLIBC_2.17)(64bit)` 依赖，`rpm -ivh` 失败。

### 与 PR 变更的关联
- **直接关联**：本次 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（+69 行），其中第 22 行硬编码了 `aarch64` 架构的 FoundationDB RPM 下载 URL。这是 PR 引入的全新代码，触发了本次失败。
- 历史知识库（模式18、模式10）指出该 PR 还存在其他潜在问题（git 浅克隆与 commit hash checkout 不兼容、boost-foundation 包名有误），但这些问题在当前日志中未被触发，因为构建在更早的 RPM 安装步骤就失败了。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的硬编码架构字符串 `aarch64` 替换为 Docker BuildKit 提供的 `TARGETARCH` 变量（BuildKit 内置 ARG，值为 `amd64` 或 `arm64`），使 Dockerfile 在不同架构的 CI 构建任务中均能下载对应架构的 RPM。需注意 FoundationDB 发布的 RPM 文件名中架构标识为 `x86_64`（非 `amd64`）和 `aarch64`，需在 Dockerfile 中做映射转换。

### 方向 2（置信度: 中）
若 FoundationDB 不提供 x86_64 架构的 RPM（仅发布 aarch64），则需改用 FoundationDB 的二进制 tar 包安装方式，或从源码编译 FoundationDB 客户端库。

## 需要进一步确认的点
1. **FoundationDB 7.3.77 是否发布 x86_64 RPM**：需确认 `https://github.com/apple/foundationdb/releases/download/7.3.77/` 下是否存在 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`。
2. **浅克隆与 commit hash checkout 问题（模式18）**：当前 Dockerfile 使用 `git clone --depth 1` + `git checkout ${VERSION} 2>/dev/null || true`，`|| true` 掩盖了浅克隆无法 checkout 历史 commit 的错误。修复方向 1 后，需验证该问题是否导致后续 cmake 构建阶段产出错误版本。
3. **包名有效性（模式10）**：历史知识库提示 `boost-foundation` 包名可能在 openEuler 24.03 中不存在。修复方向 1 后，需在 yum install 阶段和运行时 yum install 阶段验证所有包名。

## 修复验证要求
1. **架构 URL 验证**：code-fixer 在修改 Dockerfile 前，需确认 Apple FoundationDB GitHub Releases 页面（7.3.77 版本）中同时存在 `x86_64` 和 `aarch64` 两种架构的 RPM 文件，且文件名格式一致（仅架构后缀不同）。
2. **多架构构建验证**：修复后需在 x86_64 和 aarch64 两种架构的 CI 环境上验证 Docker build 均能通过 `[5/9]` 步骤。
3. **下游步骤完整性**：由于当前构建在步骤 5/9 就失败了，步骤 6-9（git clone + cmake 编译、yum remove、运行时 yum install）尚未被验证。code-fixer 修复后需确保所有后续步骤也能通过。
