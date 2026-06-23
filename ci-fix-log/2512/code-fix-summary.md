# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码 aarch64 架构，导致 x86_64 CI 构建失败；同时修复 git clone --depth 1 与 commit hash checkout 不兼容的潜伏问题，以及 clang 库路径硬编码 aarch64 的问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  1. 新增多阶段构建：`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`，通过 `COPY --from=fdb` 获取 FoundationDB 客户端二进制（`fdbcli`、`libfdb_c.so`），替代原有的 RPM 下载安装方式，彻底避免架构硬编码和 RPM 依赖冲突问题。
  2. 移除 git clone 的 `--depth 1 --shallow-submodules` 参数，改为完整克隆，确保 `git checkout ${VERSION}`（commit hash `22fca04`）能正确检出。
  3. 移除 `git checkout` 和 `git submodule update` 后的 `2>/dev/null || true`，让错误在 CI 中可见而非被静默掩盖。
  4. 新增 clang 库路径架构感知逻辑：`ARCH=$(uname -m)` 动态检测架构，使 clang 库符号链接路径 `${ARCH}-openEuler-linux-gnu` 在 x86_64 和 aarch64 下均正确。
  5. 修复运行时依赖中的包名错误：`boost-foundation` → `boost-filesystem`。
  6. 为关键网络命令（`curl`、`wget`）添加 `--retry` 重试参数提高构建鲁棒性。

## 修复逻辑

CI 分析报告的三个问题均已修复：

- **根因 1（直接错误 — 架构特定 URL）**：改为从 FoundationDB 官方多架构 Docker 镜像（`foundationdb/foundationdb:7.3.77`）通过 `COPY --from=fdb` 复制二进制文件。Docker 构建时自动拉取与目标平台匹配的镜像版本，无需手动构造架构特定的 URL。已从上游 `7.3.77` tag 的 FoundationDB Dockerfile 验证 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 路径存在且正确，正则/路径匹配无需调整。

- **根因 2（潜伏问题 — git clone 浅克隆）**：去掉 `--depth 1` 进行完整历史克隆，确保 commit hash `22fca04` 可被 `git checkout` 检出。同时移除错误掩码 `2>/dev/null || true`，使 checkout 失败时构建明确报错。

- **根因 3（潜伏问题 — aarch64 硬编码路径）**：通过 `ARCH=$(uname -m)` 动态获取架构，clang 库符号链接路径使用变量插值 `${ARCH}-openEuler-linux-gnu`，同时支持 x86_64 和 aarch64。

## 潜在风险
- FoundationDB COPY --from=fdb 方案依赖 `foundationdb/foundationdb` 官方镜像的多架构支持（amd64 + arm64），需确认该镜像在 CI 构建环境中可正常拉取。若该镜像不再维护或 tag 变更，需同步更新 `FDB_VERSION` ARG。
- 完整 git clone（无 --depth 1）会显著增加构建时间和网络流量（3fs 仓库较大），但这是 commit hash checkout 的必要前提。
- 无其他风险。