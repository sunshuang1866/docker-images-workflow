# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM平台不兼容
- 新模式症状关键词: error: Failed dependencies, libm.so.6(GLIBC_2.17), foundationdb-clients, .el9.aarch64, rpm -ivh

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
------
Dockerfile:22
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`
- 失败原因: Dockerfile 硬编码了 aarch64 平台的 FoundationDB RPM URL（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），且该 RPM 是面向 RHEL 9（`.el9`）构建的制品，其 glibc 版本化符号依赖（`GLIBC_2.17`）在 openEuler 基础镜像上无法满足。

### 根因细化
1. **架构硬编码**：Dockerfile 中 RPM URL 固定为 `aarch64`，未使用 BuildKit 内置 `TARGETARCH` 变量或 `$(uname -m)` 进行架构自适应选择。日志中 Rust 安装步骤显示构建主机为 `x86_64-unknown-linux-gnu`（非 aarch64），URL 中的 `aarch64` 与构建目标架构不匹配。
2. **发行版不兼容**：FoundationDB 官方发布的是 RHEL 9（`.el9`）RPM，其依赖声明引用了 glibc 版本化符号 `libm.so.6(GLIBC_2.17)`。openEuler 并非 RHEL 衍生发行版，rpm 依赖解析器无法将此符号与 openEuler 的 glibc 包匹配，导致依赖失败。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（新增 69 行），其中第 22 行的 FoundationDB RPM 安装步骤直接触发了此失败。该失败完全由本次 PR 引入，非已有问题。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 安装方式改为直接从 FoundationDB 官方容器镜像 COPY 二进制文件（多阶段构建），绕过 RPM 依赖解析问题。FoundationDB 官方提供 `foundationdb/foundationdb:7.3.77` 容器镜像，可在 Dockerfile 中通过 `COPY --from` 提取所需客户端二进制。

### 方向 2（置信度: 中）
保持 RPM 安装方式，但增加架构自适应逻辑：
- 使用 `TARGETARCH`（`ARG TARGETARCH`）或 `$(uname -m)` 动态选择 `x86_64` 或 `aarch64` RPM URL
- 使用 `rpm -ivh --nodeps` 跳过依赖检查，然后手动安装缺失的运行时库（但需确认 FoundationDB 客户端在 openEuler 上实际可用）

### 方向 3（置信度: 低）
从 FoundationDB 源码编译构建客户端库，完全避免预编译 RPM 的平台兼容性问题（但构建复杂度显著增加，不推荐）。

## 需要进一步确认的点

1. **FoundationDB 客户端是否实际需要**：确认 3FS 构建过程中 FoundationDB 客户端（`fdbcli` 等）是否为硬性依赖，还是仅用于运行时。如果是运行时依赖，可考虑将 RPM 安装移到最终镜像阶段而非构建阶段。
2. **多架构支持**：确认 CI 流水线是否同时构建 x86_64 和 aarch64 两个架构的镜像，以便判断是否需要架构自适应逻辑。
3. **历史模式 18（git 浅克隆与 commit hash checkout 不兼容）**：知识库中已记录此 PR 存在 `git clone --depth 1` + commit hash checkout 不兼容问题（`Dockerfile:27-30`），虽然当前 CI 日志中此步骤尚未执行（构建在第 10 步即失败），但修复 FoundationDB 问题后该步骤将执行，可能触发后续失败。需一并检查 `git clone` 步骤的正确性。
4. **FoundationDB 官方镜像可用性**：确认 Docker Hub 上 `foundationdb/foundationdb:7.3.77` 标签是否存在，是否同时提供 x86_64 和 aarch64 架构。

## 修复验证要求

若采用方向 1（多阶段构建 COPY），code-fixer 必须：
- 在修复后的 Dockerfile 中明确引用 FoundationDB 官方镜像的准确 tag（如 `foundationdb/foundationdb:7.3.77`）
- 验证 FoundationDB 客户端二进制在 openEuler 基础镜像上直接运行时无额外 glibc 兼容性问题
- 同时处理历史模式 18（git 浅克隆问题），确保 `git clone` 步骤的 checkout 逻辑能正确拉取指定 commit hash `22fca04`
