# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM 平台不兼容
- 新模式症状关键词: `error: Failed dependencies:`, `libm.so.6(GLIBC_2.17)`, `el9.aarch64.rpm`, `foundationdb-clients`, `rpm -ivh`

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
- 失败原因: Dockerfile 下载了 FoundationDB 官方提供的 RHEL 9 aarch64 RPM 包（`el9.aarch64.rpm`），该 RPM 依赖 `libm.so.6(GLIBC_2.17)` 版本化符号，但 openEuler 24.03-LTS-SP3 的 glibc 不提供该版本符号，导致 `rpm -ivh` 依赖检查失败。

### 与 PR 变更的关联
此 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（+69 行），整个 3FS 镜像构建文件为该 PR 首次引入。FoundationDB RPM 安装步骤（第 22-24 行）完全由本次 PR 新增，失败与 PR 变更直接相关。

## 影响范围评估
- **直接影响**: 3FS 镜像构建在 `rpm -ivh foundationdb-clients` 步骤失败，Docker 构建无法完成。
- **架构影响**: Dockerfile 硬编码了 `aarch64` RPM URL，而日志显示 rustup 检测到 `x86_64-unknown-linux-gnu` 宿主机三元组（`#8 1.022 info: default host triple is x86_64-unknown-linux-gnu`），因此该步骤在 **x86_64 架构**上还存在架构不匹配的额外隐患。
- **次级风险（模式18）**: Dockerfile 中 `git clone --depth 1` + `git checkout ${VERSION} 2>/dev/null || true`（`VERSION=22fca04` 为 7 字符 commit hash）存在浅克隆无法 checkout 指定历史 commit 的风险，`|| true` 掩盖了 checkout 失败，导致可能编译错误的代码版本（历史知识库 模式18 已记录此问题）。

## 修复方向

### 方向 1（置信度: 高）
**不从 GitHub Releases 下载 FoundationDB RPM，改为从 FoundationDB 官方 Docker 镜像中提取客户端二进制（多阶段构建）或从源码编译。**

FoundationDB 官方只发布面向 RHEL/CentOS 的 RPM 包，这些 RPM 的 glibc 版本依赖与 openEuler 不兼容。替代方案：
- 多阶段构建：`FROM foundationdb/foundationdb:7.3.77 AS fdb-source`，然后 `COPY --from=fdb-source /usr/bin/fdbcli /usr/local/bin/` 等
- 或从 FoundationDB 源码编译客户端库

### 方向 2（置信度: 中）
**尝试用 `rpm -ivh --nodeps` 强制安装并手动创建缺失的符号链接。**

如果 openEuler 的 `libm.so.6` 实际提供了等价功能但版本符号不同，可用 `--nodeps` 跳过依赖检查。此方案有运行时风险，需在 live container 中验证 FoundationDB 客户端是否正常工作。

### 方向 3（模式18关联修复，置信度: 高）
**修复 shallow clone + commit hash checkout 问题。**

将 `git -C /tmp/3fs checkout ${VERSION} 2>/dev/null || true` 改为先 `git fetch --depth 1 origin ${VERSION}` 再 `git checkout FETCH_HEAD`，或去掉 `--depth 1`。此问题虽未导致本次构建失败（被 `|| true` 掩盖），但会导致编译错误的代码版本。

## 需要进一步确认的点
1. FoundationDB 官方仓库 `apple/foundationdb` 是否有适用于 openEuler 或其他 Linux 发行版的二进制发布格式（tar.gz 等）
2. openEuler 24.03-LTS-SP3 的 glibc 实际版本号，以及 `libm.so.6` 提供的 GLIBC 版本符号列表
3. 该 Dockerfile 的 x86_64 架构构建是否需要不同的 FoundationDB RPM URL（当前硬编码 `aarch64`）
4. 3FS 项目对 FoundationDB 客户端的实际运行时需求（仅需 `fdbcli` 还是需要完整的 client libraries）

## 修复验证要求
若修复方向采用多阶段构建（方向 1），code-fixer 必须在提交前：
- 在 openEuler 24.03-LTS-SP3 容器中验证 `COPY --from` 提取的 FoundationDB 二进制能正常运行（`fdbcli --version` 不报错）
- 同时在 x86_64 和 aarch64 两种架构上验证构建成功
- 验证方向 3（shallow clone 修复）后，确认 `git checkout ${VERSION}` 确实 checkout 到了指定 commit `22fca04`
