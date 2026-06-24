# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码不匹配
- 新模式症状关键词: `Failed dependencies`, `aarch64`, `x86_64`, `rpm -ivh`, `foundationdb-clients`, `GLIBC`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm \
    https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
    rpm -ivh /tmp/fdb-clients.rpm && \
    rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
------
Dockerfile:22
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构后缀，但本次构建运行在 x86_64 平台上（meson 在 #9 步输出 `Host machine cpu family: x86_64`），导致下载的 aarch64 架构 RPM 无法在 x86_64 系统上安装，rpm 报依赖缺失（实际是架构不兼容）。

### 与 PR 变更的关联
PR #2512 的两类变更：
1. **目录重命名**（`.agents/` → `.claude/`）：仅文件名和路径引用变更，与构建失败无关。
2. **新增 3FS Dockerfile**（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，69 行新增）：该文件全新引入，第 22 行硬编码 `aarch64` 在 RPM URL 中，直接导致本次 x86_64 构建失败。

**结论：本次失败直接由 PR 新增的 Dockerfile 中的架构硬编码缺陷引起。**

### 影响范围评估
- 局部问题：仅影响 3FS 镜像构建。
- 该 Dockerfile 对 x86_64 和 aarch64 两架构均使用同一硬编码 aarch64 URL，因此 **x86_64 构建必然失败**，aarch64 构建可能通过（取决于 FDB 7.3.77 aarch64 RPM 对 openEuler 24.03 上可用依赖的实际兼容性）。

### 潜在后续失败点（本次日志未触发，但代码中存在）
Dockerfile 中还有以下已知风险（历史模式已记录）：
- **模式18（git 浅克隆与 commit hash checkout 不兼容）**：`git clone --recurse-submodules --depth 1 ... && git checkout ${VERSION} 2>/dev/null || true` 中 `--depth 1` 浅克隆后无法 checkout 非最新 commit hash，且 `|| true` 静默掩盖了错误。本次构建在步骤 #10（FDB RPM）即失败，未执行到该步骤，但若 FDB 安装修复后 x86_64 构建能到达该步，该问题仍会导致后续构建失败。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 FDB RPM 安装步骤中，使用 BuildKit 预定义变量 `TARGETARCH` 或 shell 命令检测当前架构，从 FoundationDB GitHub Releases 下载对应架构的 RPM：
- x86_64 构建时：下载 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`
- aarch64 构建时：下载 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`

注意：openEuler 24.03-LTS-SP3 并非 el9 系发行版，即使架构正确，FDB RPM 的 glibc 版本要求（`GLIBC_2.17`）是否与 openEuler 实际 glibc 兼容仍需验证。若 RPM 安装成功后运行时仍有 so 链接问题，可能需要改用从源码编译 FoundationDB 客户端，或使用 FDB 官方 Docker 镜像多阶段 COPY。

### 方向 2（置信度: 高）
修复 git 浅克隆与 commit hash checkout 不兼容问题（模式18）：将 `git checkout ${VERSION} 2>/dev/null || true` 改为先 `git fetch origin ${VERSION}` 再 `git checkout FETCH_HEAD`，或直接去掉 `--depth 1` 参数，确保指定 commit hash 能被正确 checkout 且不静默失败。

## 需要进一步确认的点
1. **FoundationDB 7.3.77 x86_64 RPM 对 openEuler 24.03 的兼容性**：需确认 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 在 openEuler 24.03-LTS-SP3 容器中能否正常安装（glibc 符号版本兼容性），若不行需要换用其他安装方式（如源码编译或多阶段 COPY）。
2. **aarch64 构建日志**：本次提供的日志来自 x86_64 构建（meson 输出 `x86_64`），aarch64 构建可能遇到不同问题（如 FDB aarch64 RPM 的依赖在 openEuler 上的可用性、`clang` 库路径中的 aarch64 特定路径是否正确），需要获取 aarch64 构建 job 的完整日志才能确认。
3. **YAML 元数据校验**：历史模式 11 已记录该 PR 存在 `.claude/README.md` 路径不符合 appstore 发布规范的问题，当前修复是否已解决该问题需验证。
4. **上游 commit `22fca04` 的可用性**：VERSION 使用 7 字符短 hash，在浅克隆场景下（`--depth 1`）无法被 Git 解析为远程 ref，必须先修复 git 克隆方式后方能验证该 hash 是否对应有效提交。

## 修复验证要求
- **FDB RPM 架构修复后**：需在 x86_64 和 aarch64 两个架构的 openEuler 24.03-LTS-SP3 容器中分别验证 RPM 安装成功。
- **git checkout 修复后**：需验证在 x86_64 和 aarch64 构建中 `git checkout 22fca04` 能成功切换（输出 `HEAD is now at 22fca04...` 或类似信息），不允许 checkout 失败被 `|| true` 静默跳过。
- **全构建验证**：修复上述问题后，需触发完整的 x86_64 和 aarch64 CI 构建，验证从 yum 安装到 cmake 编译的全流程均能通过，因为本次日志仅走到 5/9 步即失败，后续 4 个步骤（git clone、cmake 配置、cmake 编译、运行时库安装）尚未经过实际验证。
