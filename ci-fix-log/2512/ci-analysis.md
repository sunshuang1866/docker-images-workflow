# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: el9 RPM glibc 依赖不兼容
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6(GLIBC_2.17)`, `needed by`, `el9`, `rpm -ivh`, `foundationdb`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  21 |     
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
  25 |     
--------------------
ERROR: failed to solve: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB 官方仅发布面向 RHEL/CentOS 9 (`el9`) 的 aarch64 RPM 包，其 `rpm` 元数据中硬编码了对 `libm.so.6(GLIBC_2.17)(64bit)` 版本化符号的依赖，而 openEuler 24.03-lts-sp3 的 glibc 构建产出的 `libm.so.6` 未提供该 ELF symbol version 标签，导致 `rpm -ivh` 依赖解析失败。

### 与 PR 变更的关联
**直接由 PR 引入。** 该失败发生在 PR 新增的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 第 22-24 行，即 FoundationDB clients RPM 安装步骤。此 Dockerfile 是本 PR 新增的核心文件，不涉及任何已有代码的回归问题。

### 已知的后续隐患
知识库模式 18 已记录本 PR 在同 Dockerfile 中还存在另一个独立问题：`git clone --depth 1` 浅克隆后无法 checkout 指定 commit hash `22fca04`（第 33-34 行），且 `2>/dev/null || true` 静默掩盖了该错误。当前构建在第 22 行已失败，尚未执行到该步骤，但修复 FoundationDB 问题后该问题将成为下一个阻塞点。

## 修复方向

### 方向 1（置信度: 高）
FoundationDB 官方 RPM 与 openEuler glibc 存在 ABI-level symbol versioning 不兼容，直接安装不可行。改为**从 FoundationDB 官方 Docker 镜像中多阶段复制二进制文件**（参考模式 16 的修复思路），绕过 RPM 安装步骤：

```
FROM foundationdb/foundationdb:7.3.77 AS fdb-source
FROM openeuler/openeuler:24.03-lts-sp3
COPY --from=fdb-source /usr/bin/fdbcli /usr/local/bin/
COPY --from=fdb-source /usr/lib/libfdb_c.so /usr/local/lib64/
# 以及 3FS cmake 编译所需的其他 fdb 头文件和库
```

注意：FoundationDB 官方基础镜像很可能也是基于某种 Linux 发行版（如 Ubuntu），从中复制的二进制可能仍需确认与 openEuler 的 ABI 兼容性。code-fixer 在提交前必须在 live openEuler 容器中验证复制后的 `fdbcli` 和 `libfdb_c.so` 能否正常运行。

### 方向 2（置信度: 中）
尝试 `rpm -ivh --nodeps` 强制安装。风险：FoundationDB clients 二进制在运行时可能因缺少实际 glibc 2.17 符号版本支持而 crash。如果 `--nodeps` 后 FoundationDB 客户端可正常运行，则这是最简单的修复；否则仍需回退到方向 1。

### 方向 3（置信度: 低）
从 FoundationDB 源码编译 clients library。FoundationDB 使用 CMake 构建系统，理论上可以从源码编译出适配 openEuler 的客户端库。但 FoundationDB 构建链路复杂（依赖 boost、flow 等内部组件），编译时间和成功率均不确定，仅作为最后手段。

## 需要进一步确认的点

1. **FoundationDB 7.3.77 官方 Docker 镜像的具体二进制布局**：需拉取 `foundationdb/foundationdb:7.3.77` 查看 `/usr/bin/` 和 `/usr/lib*/` 下的文件列表，确认 3FS CMake 编译所需的所有文件（`libfdb_c.so` 以及头文件 `fdb_c.h` 等），确保 `COPY --from` 的路径正确。
2. **跨发行版 ABI 验证**：FoundationDB 官方镜像基于 Ubuntu/CentOS，从中复制的二进制在 openEuler 24.03 上是否可直接运行，需在 live 容器中实测。
3. **3FS 运行时对 FoundationDB 的依赖程度**：确认 3FS 的 `mgmtd_main`、`meta_main`、`storage_main` 在运行时是否动态链接 `libfdb_c.so`，如果是则必须确保运行库路径（`LD_LIBRARY_PATH`）中包含复制后的 `.so` 路径。
4. **git clone 浅克隆问题**（知识库模式 18）：修复 FoundationDB 问题后，Dockerfile 第 33-34 行的 `git clone --depth 1` + commit hash checkout 问题将成为下一个阻塞点，需一并处理。

## 修复验证要求
若采用方向 1（多阶段复制）：
1. code-fixer 必须从 `foundationdb/foundationdb:7.3.77` 镜像中确认 `libfdb_c.so`、`fdbcli`、`fdb_c.h` 等文件的实际路径。
2. 必须在 openEuler 24.03-lts-sp3 live 容器中验证复制后的 `libfdb_c.so` 可被 `ldd` 正常解析（无 missing 依赖），且 `fdbcli --version` 可正常输出。
3. 必须在全量 Docker 构建中验证 cmake 配置阶段能正确找到 FoundationDB 头文件和库（CMake 的 `FindFoundationDB` 或自定义 `-DFDB_LIBRARY`/`-DFDB_INCLUDE_DIR` 参数可能需要调整）。

若采用方向 2（--nodeps）：
1. code-fixer 必须在 openEuler live 容器中 `rpm -ivh --nodeps` 后运行 `ldd /usr/lib*/libfdb_c.so` 确认无缺失动态链接库，并执行 `fdbcli --version` 验证运行时正常。
