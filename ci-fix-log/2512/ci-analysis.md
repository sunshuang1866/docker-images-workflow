# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨发行版RPM依赖不兼容
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6(GLIBC_2.17)`, `el9.aarch64.rpm`, `rpm -ivh`, foundationdb-clients

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
- 失败原因: `foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 是面向 RHEL/CentOS 9 (`.el9`) 构建的 RPM 包，其 RPM 元数据声明的依赖 `libm.so.6(GLIBC_2.17)(64bit)` 在 openEuler 的 glibc 打包体系下无法被满足，导致 `rpm -ivh` 依赖解析失败。同时该 RPM 文件名硬编码了 `aarch64` 架构，但 CI 构建日志显示宿主为 x86_64，存在架构不匹配。

### 与 PR 变更的关联
本次 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行新文件），其中第 22-24 行的 `RUN` 指令直接下载并安装 FoundationDB 客户端 RPM。该 RPM 依赖 openEuler 无法满足，且架构硬编码与 CI 构建环境不匹配，是 PR 变更直接触发的失败。

**注**: 历史知识库中已记录该 PR 的另外两个已知问题（模式18：`git clone --depth 1` + commit hash checkout 不兼容；模式10：`boost-foundation` 包名不存在及缺少构建依赖），但本次 CI 失败发生在更早的 FoundationDB RPM 安装步骤，尚未到达 git 和 cmake 构建阶段。

## 修复方向

### 方向 1（置信度: 高）
**改用多阶段构建从 FoundationDB 官方 Docker 镜像复制客户端二进制**。FoundationDB 官方提供 `foundationdb/foundationdb:7.3.77` 容器镜像，其中包含 `fdbcli` 等客户端工具。可以在 Dockerfile 中增加一个构建阶段 `FROM foundationdb/foundationdb:7.3.77 AS fdb-source`，然后用 `COPY --from=fdb-source` 将所需二进制文件复制到 openEuler 最终镜像中，替代 `rpm -ivh` 安装方式。此方案同时规避了跨发行版 RPM 依赖问题和架构硬编码问题。

### 方向 2（置信度: 中）
**从 FoundationDB 官方 RPM 仓库获取 openEuler 兼容的 RPM 或使用 `--nodeps` 强制安装后手动处理依赖**。FoundationDB 官方可能提供多发行版的 RPM，可检查是否有 `.el8` 或其他兼容版本；或者用 `rpm -ivh --nodeps` 绕过依赖检查后，手动创建缺失的 library symlink。但此方向风险较高，可能引入运行时不稳定。

### 方向 3（置信度: 低）
**在 Dockerfile 中增加架构判断，动态选择 x86_64 / aarch64 的 RPM URL**，并用 `--nodeps` 安装。此方案只解决架构硬编码问题，不解决跨发行版 RPM 依赖的根本矛盾。

## 需要进一步确认的点
1. 确认 CI 构建的架构（日志中 fuse 构建检测到 `x86_64` 宿主，但 RPM URL 硬编码 `aarch64`——需确认是否有独立的 aarch64 CI job 以及该 job 上 FoundationDB RPM 的具体安装表现）
2. 确认 FoundationDB 7.3.77 官方 Docker 镜像的具体路径和所需二进制文件的文件名（`fdbcli`、`fdbserver`、`fdbmonitor` 等），以便正确编写 COPY 指令
3. 确认 3FS 项目实际需要的 FoundationDB 客户端组件列表（是否只需要 `fdbcli`，还是需要完整的 FoundationDB 客户端库 `libfdb_c.so`）
4. 历史知识库中已记录的该 PR 另外两个问题（模式18: git shallow clone 不兼容 commit hash checkout；模式10: 构建依赖缺失）在 FoundationDB 问题修复后可能仍然会导致后续构建失败，需要在本次修复后一并验证
