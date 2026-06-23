# 修复摘要

## 修复的问题
Dockerfile 中三处架构硬编码（FoundationDB RPM aarch64 固定 URL、shallow clone 导致的 git checkout 失败、Clang 库路径硬编码 aarch64）导致在 x86_64 构建环境上失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 三处修复

## 修复逻辑

已通过以下改动（由 fix 分支的先前提交完成）解决 CI 分析报告指出的全部三个根因：

1. **FoundationDB RPM 架构硬编码（根因 #1）**：将 `curl` 下载 aarch64 RPM 并 `rpm -ivh` 的方式替换为多阶段构建，通过 `COPY --from=fdb` 从 `foundationdb/foundationdb` 官方镜像复制 `fdbcli` 和 `libfdb_c.so`，彻底消除架构依赖。

2. **Shallow clone + git checkout 不兼容（根因 #2）**：移除 `git clone` 的 `--depth 1 --shallow-submodules` 参数，改为完整克隆；同时移除 `git checkout` 和 `git submodule update` 的 `2>/dev/null || true` 错误抑制，使 checkout 失败能正确暴露。

3. **Clang 库路径硬编码 aarch64（根因 #3）**：将硬编码的 `aarch64-openEuler-linux-gnu` 和 `libclang_rt.builtins-aarch64.a` 替换为 `` ARCH=$(uname -m) `` 动态确定的 `${ARCH}` 变量，使构建适配 x86_64 和 aarch64 两种架构。

## 潜在风险
- 多阶段构建 `COPY --from=fdb` 依赖 FoundationDB 官方镜像的目录结构（`/usr/bin/fdbcli`、`/usr/lib/libfdb_c.so`），若官方镜像未来调整这些路径，构建将失败。
- 完整 `git clone`（无 `--depth 1`）会增加网络流量和克隆时间，对于大型仓库可能需要更多 CI 资源。