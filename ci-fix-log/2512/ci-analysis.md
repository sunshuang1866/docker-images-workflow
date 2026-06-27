# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM 跨发行版依赖不兼容
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6(GLIBC_2.17)(64bit)`, `foundationdb-clients`, `.el9.aarch64.rpm`, `openEuler`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`（`RUN curl ... fdb-clients.rpm && rpm -ivh ...`）
- 失败原因: Dockerfile 下载并尝试安装 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`，该 RPM 是为 RHEL/CentOS 9（el9）构建的，其 RPM 依赖 `libm.so.6(GLIBC_2.17)(64bit)` 在 openEuler 24.03-lts-sp3 基础镜像上无法被 RPM 依赖解析器满足——openEuler 的 glibc 打包方式与 EL9 不同，提供的 RPM provides 元数据不匹配该 RPM 的要求。此外，RPM 文件名为 `.aarch64.rpm`，但日志中 meson 和 rustup 均报告构建环境为 `x86_64`，存在潜在的架构不匹配问题。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，其中第 22-24 行直接引入了下载安装 foundationdb-clients RPM 的 `RUN` 步骤。该步骤是本次 PR 首次添加的，与失败直接相关。PR 的 `.claude/` 目录下文件变更（CLAUDE.md 内容修改、agents/README.md 重命名为 README.md、.pyc 文件删除）与本次构建失败无关。

## 修复方向

### 方向 1（置信度: 高）
**绕过 RPM 安装，改用 FoundationDB 官方多阶段构建复制二进制**。参考 historical_patterns 模式 16（RPM 包停止发布 → 换多阶段构建绕过），从 FoundationDB 官方容器镜像（如 `foundationdb/foundationdb:7.3.77`）中 `COPY --from` 提取 `fdbcli` 等所需客户端二进制文件，替代从 GitHub Releases 下载 EL9 aarch64 RPM 的做法。这可以同时解决发行版兼容性问题和架构匹配问题。

### 方向 2（置信度: 中）
**安装 glibc 兼容层或使用 `--nodeps` 强制安装**。通过 `rpm -ivh --nodeps /tmp/fdb-clients.rpm` 跳过依赖检查强制安装（RPM 的实际二进制文件可能可以运行），或补充安装 openEuler 上提供等效共享库的兼容包。此方向有风险：绕过依赖可能导致运行时动态链接失败。

### 方向 3（置信度: 低）
**从 FoundationDB 源码编译客户端**。克隆 FoundationDB 仓库，在 openEuler 上从源码构建客户端工具。此方向构建时间长且可能引入新的编译依赖问题。

## 需要进一步确认的点
1. **构建架构确认**: 日志中 meson 和 rustup 均报告 `x86_64`，但 RPM 为 `.aarch64.rpm`。需确认 CI 构建是否使用了 `docker buildx --platform linux/amd64` 还是 `linux/arm64`。如果构建目标是 x86_64，则需要 x86_64 版本的 foundationdb-clients（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm`）；如果构建目标是 aarch64，则需要排查为何 meson/rustup 报告 x86_64。
2. **FoundationDB 上游是否有 openEuler 兼容的 RPM 发布**: 检查 FoundationDB GitHub Releases 是否提供其他架构（x86_64）或通用 Linux 格式的客户端包。
3. **`.claude/` 目录路径变更是否符合 CI appstore 预检规范**: historical_patterns 模式 11 中记录了 PR #2512 的 `.claude/agents/README.md` 重命名为 `.claude/README.md` 触发了 CI appstore 发布规范预检失败（期望路径为 `.claude/README.md` 但实际提交可能不符合校验）。当前 CI 日志未包含预检阶段的输出，如果上游 CI pipeline 中预检步骤先于 Docker 构建执行，此问题可能已被修复或仍需处理。需确认 `.claude/README.md` 的最终路径是否符合 appstore 规范要求。
4. **git 浅克隆问题**: historical_patterns 模式 18 记录了 `git clone --depth 1` + commit hash checkout 不兼容的问题（同 PR）。当前日志中第 9 步之后的步骤被截断，无法确认后续的 `git clone` 和 cmake 构建步骤是否成功。如果 RPM 问题修复后构建继续，可能存在此后续问题。

## 修复验证要求
- 使用 FoundationDB 官方镜像提取二进制的方式（方向 1）时，需验证目标二进制文件（`fdbcli` 等）在 openEuler 24.03-lts-sp3 基础镜像上运行时动态链接库是否满足，可用 `ldd` 检查。
- 如果改用 `--nodeps`（方向 2），必须在容器启动后验证 `fdbcli --version` 是否能正常执行。
- 修复后需触发完整的 Docker 构建流程，验证 RPM 安装之后的 git clone + cmake 构建步骤也能顺利通过。
