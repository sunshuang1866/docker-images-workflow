# 修复摘要

## 修复的问题
FoundationDB 客户端 RPM 下载 URL 硬编码 `aarch64` 架构，导致 x86_64 CI 构建时依赖检查失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 客户端的安装方式从硬编码架构的 RPM 下载改为多阶段构建（`COPY --from=fdb`），从官方 `foundationdb/foundationdb:7.3.77` 多架构镜像直接复制二进制文件。同时修复了 git 浅克隆导致无法 checkout commit hash 的问题（移除 `--depth 1` 和 `|| true` 静默掩盖），并添加了 clang 库路径的架构自适应支持（`ARCH=$(uname -m)`）。

## 修复逻辑

CI 分析报告根因：Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 和 `el9`，在 x86_64 构建环境中 `rpm -ivh` 因依赖声明不匹配而失败。

当前代码已通过以下方式彻底解决该问题：
1. **多阶段构建替代 RPM 安装**：使用 `FROM foundationdb/foundationdb:7.3.77 AS fdb`（该镜像为官方多架构镜像，Docker 会自动拉取与构建平台匹配的架构变体），然后通过 `COPY --from=fdb` 复制 `fdbcli` 和 `libfdb_c.so`。已从上游 release-7.3 获取 `packaging/docker/Dockerfile` 验证，确认 `libfdb_c.so` 位于 `/usr/lib/libfdb_c.so`，`fdbcli` 位于 `/usr/bin/fdbcli`，COPY 路径正确。
2. **Git 克隆修复**：移除 `--depth 1` 和 `|| true` 静默忽略，改为完整克隆，确保 `git checkout ${VERSION}`（commit hash）能正常工作。
3. **Clang 架构自适应**：通过 `ARCH=$(uname -m)` 动态确定 clang 库路径，支持 x86_64 和 aarch64 双架构。

无额外代码修改需要——上述修复已全部在 `fix/2512` 分支中生效。

## 潜在风险
- `/usr/lib64/libfdb_c.so` 作为目标路径依赖 openEuler 动态链接器的默认搜索路径。如果 openEuler 的 `ldconfig` 配置中 `/usr/lib64/` 不在默认搜索范围内，3FS 运行时可能找不到该库。当前通过 `LD_LIBRARY_PATH` 设置了 `/opt/3fs/lib:/usr/local/lib`，但未显式包含 `/usr/lib64/`。若 CI 后续步骤（3FS 编译/链接）报告找不到 `libfdb_c.so`，需将 `/usr/lib64/` 加入 `LD_LIBRARY_PATH`。