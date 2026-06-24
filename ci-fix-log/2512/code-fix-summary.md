# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB RPM 下载 URL 硬编码 `aarch64` 架构后缀，导致 x86_64 构建中 RPM 架构不兼容安装失败；同时修复了 git 浅克隆导致 commit hash checkout 静默失败的潜在风险，以及 clang 库路径中硬编码架构问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  1. 用多阶段 `COPY --from=fdb`（从 `foundationdb/foundationdb:${FDB_VERSION}` 镜像）替代硬编码 `aarch64` 的 RPM 下载安装，实现跨架构兼容
  2. 移除 `git clone` 的 `--depth 1 --shallow-submodules` 参数，使完整历史克隆支持任意 commit hash checkout
  3. 移除 `git checkout ${VERSION} 2>/dev/null || true` 中的 `|| true`，确保 checkout 失败不再被静默掩盖
  4. 添加 `ARCH=$(uname -m)` 动态架构检测，替换 clang 库路径中硬编码的 `aarch64` 为 `${ARCH}` 变量
  5. 移除 pr-head 版本中临时添加的 sed 补丁命令和非必要的 yum/编译依赖

## 修复逻辑
CI 失败分析报告指出两个根因：

**根因 1（直接错误）**：第 22-24 行 FDB RPM 安装 URL `foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 硬编码 aarch64，x86_64 构建时 rpm 报 "Failed dependencies"（实际是架构不兼容）。修复方案采用分析报告方向 1 的建议——使用 FDB 官方 Docker 镜像多阶段 COPY，即 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` + `COPY --from=fdb`，此为架构无关方案。

**根因 2（潜在后续失败，分析报告方向 2）**：`git clone --depth 1` 浅克隆后无法 checkout 非最新 commit hash，且 `|| true` 静默掩盖错误。修复方案：移除 `--depth 1` 和 `--shallow-submodules` 做完整克隆，同时移除所有 `|| true` 以确保 checkout 失败时显式报错。

**附带修复**：clang 路径中 `aarch64-openEuler-linux-gnu` 硬编码改为 `${ARCH}-openEuler-linux-gnu`，使用 `uname -m` 动态检测。

## 潜在风险
- FDB 多阶段 COPY 方式依赖 `foundationdb/foundationdb:7.3.77` 镜像需同时支持 amd64 和 arm64 架构（该镜像通常为多架构 manifest）
- 完整 git clone（无 `--depth 1`）相比浅克隆增加了网络传输量和构建时间
- 本次构建日志仅执行到步骤 5/9 即失败，后续 git clone、cmake 配置/编译、运行时库安装步骤尚未在 CI 中验证
- 移除的 sed 补丁命令（coroutines/Werror/tests/benchmarks）和 cmake flags 可能仍为必要，若后续构建失败需按需恢复