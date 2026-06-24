# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码不匹配
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6(GLIBC_2.17)`, `aarch64`, `rpm -ivh`, `foundationdb-clients`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
------
Dockerfile:22
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），但当前 CI build 运行在 **x86_64** 平台（日志中 meson 报告 `Host machine cpu family: x86_64`，rust 报告 `default host triple is x86_64-unknown-linux-gnu`）。aarch64 RPM 依赖的 `libm.so.6(GLIBC_2.17)(64bit)` 在 x86_64 系统的 RPM 数据库中无法解析，导致依赖检查失败。

### 与 PR 变更的关联
PR #2512 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（全新文件，69 行），该 Dockerfile 第 22 行的 FoundationDB RPM 下载 URL 直接硬编码了 `aarch64` 架构字符串。这是 PR 引入的全新构建逻辑，该失败由此新 Dockerfile 直接触发。该 Dockerfile 在 CI 中首次构建即失败。

## 修复方向

### 方向 1（置信度: 高）
Dockerfile 中 FoundationDB RPM 下载 URL 需要根据目标架构动态选择：x86_64 使用 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`，aarch64 使用 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`。可利用 Docker BuildKit 的 `TARGETARCH` 预定义 ARG（值为 `amd64` 或 `arm64`）结合 shell 条件判断构造正确的 URL。

### 方向 2（置信度: 中）
若 FoundationDB 在 openEuler 上无法通过 RPM 直接安装（el9 RPM 与 openEuler 的 glibc ABI 可能不完全兼容），可改用 FoundationDB 官方提供的 Linux 通用 tar 包或源码编译方式替代 RPM 安装。

## 需要进一步确认的点
1. FoundationDB 7.3.77 的 x86_64 RPM 在 openEuler 24.03-lts-sp3 上是否能真正通过依赖检查并正常安装（el9 RPM 与 openEuler 可能存在 glibc 版本差异，虽当前报错来自架构不匹配，但修复架构后可能还会暴露 ABI 兼容性问题）。
2. 日志中 step #7（yum install）虽然显示 `Complete!`，但其安装的 `clang-tools-extra`、`gmock-devel`、`gtest-devel`、`libdwarf-devel`、`gperftools-devel` 等包在 openEuler 上的实际可用性需在 live container 中验证（PR diff 中 CLAUDE.md 已将这些包从"不可用"列表移除）。
3. 即使 FoundationDB RPM 问题修复，Dockerfile 后续的 step 6（git clone --depth 1 + commit hash checkout + cmake build）仍可能因浅克隆不兼容 commit hash 而失败（参见知识库模式18中该 PR 的历史记录），但当前日志未执行到该步，无法确认。

## 修复验证要求
code-fixer 在提交前必须：
1. 确认 FoundationDB 7.3.77 的 x86_64 RPM 可在 openEuler 24.03-lts-sp3 容器中通过 `rpm -ivh` 成功安装（无 glibc/ABI 依赖冲突）。
2. 若 RPM 方式在 openEuler 上根本不可行，需从 FoundationDB 官方 GitHub Releases 查找通用 Linux 二进制包或源码构建方案作为替代。
3. 修复后在 live container 中从 step 1 到 step 6 逐条验证每个 RUN 指令，确保不会在 FoundationDB 之后的其他步骤再次失败。
