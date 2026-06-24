# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 硬编码架构RPM不兼容
- 新模式症状关键词: Failed dependencies, libm.so.6, GLIBC_2.17, rpm -ivh, aarch64, foundationdb-clients, el9

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
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`（FoundationDB RPM 安装步骤）
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构，但当前 CI 构建环境实际运行在 x86_64 上（rust 检测到 `x86_64-unknown-linux-gnu`，meson 检测到 `Host machine cpu: x86_64`），导致 rpm 在 x86_64 系统上无法满足 aarch64 RPM 的 `libm.so.6(GLIBC_2.17)(64bit)` 依赖。

### 与 PR 变更的关联
PR #2512 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行），其中第 22 行硬编码了 aarch64 架构的 FoundationDB RPM URL：`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`。该错误由此次 PR 新增代码直接触发——Dockerfile 在 x86_64 构建节点上执行时，试图安装 aarch64 架构的 RPM 包，rpm 依赖解析失败。

其他 PR 变更（`.claude/` 目录重命名、agent 规则更新、README 文档）与本次 CI 构建失败无关。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的架构标识从硬编码 `aarch64` 改为根据构建平台动态选择。FoundationDB 在 GitHub Releases 中同时提供 `x86_64` 和 `aarch64` 两种架构的 RPM。Dockerfile 应使用 BuildKit ARG（如 `TARGETARCH`）或 shell 变量检测当前架构，构造正确的下载 URL（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 或 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`）。

### 方向 2（置信度: 中）
即使架构匹配，`.el9` RPM 是为 RHEL/CentOS 9 构建的，其 glibc 版本依赖（如 `GLIBC_2.17`）可能与 openEuler 24.03 的 glibc 不完全兼容。若修复架构后 RPM 安装仍报依赖错误，应考虑改用 FoundationDB 的官方 Docker 镜像多阶段构建（`COPY --from`）绕过 RPM 依赖问题，或从 FoundationDB 源码编译。

## 需要进一步确认的点
1. 需确认 CI 流水线中 x86_64 和 aarch64 构建节点是否分别独立执行此 Dockerfile——如果两个架构的 CI job 各自独立运行，则 aarch64 节点上此 URL 可能正确，只需在 x86_64 节点上修正架构。
2. 需确认 openEuler 24.03 的 glibc 是否完全提供 FoundationDB `.el9` RPM 所需的全部符号版本（`libm.so.6(GLIBC_2.17)(64bit)` 在 openEuler x86_64 上是否可用），以确定仅修正架构是否足够。

## 修复验证要求
code-fixer 在提交前必须：
1. 验证 FoundationDB 7.3.77 在 GitHub Releases 中确实存在 x86_64 架构的 RPM 文件（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm`）。
2. 在 openEuler 24.03 x86_64 容器内手动执行 `rpm -ivh` 安装该 x86_64 RPM，确认 glibc 依赖可满足、安装成功。
3. 在 openEuler 24.03 aarch64 容器内同样验证 aarch64 RPM 安装成功。
4. 确认 Dockerfile 在其他步骤（如 cmake 编译 3FS）中不会因 FoundationDB 客户端库路径或头文件位置差异而引入二次失败。
