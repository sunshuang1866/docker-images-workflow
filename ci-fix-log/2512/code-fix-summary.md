# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB RPM 下载 URL 和 clang 库路径硬编码了 `aarch64` 架构，导致 x86_64 CI 构建时架构不匹配失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 已通过多轮 fix 迭代完成以下修复（当前 HEAD 无需额外变更）：
  - FoundationDB 客户端改用多阶段构建 `COPY --from=fdb`，不再下载架构特定 RPM
  - clang 运行时库路径改用 `ARCH=$(uname -m)` 动态确定，不再硬编码 `aarch64-openEuler-linux-gnu`
  - git clone 移除 `--depth 1 --shallow-submodules`，改用完整克隆 `--recurse-submodules`，确保可 checkout 到 `22fca04` commit
  - 移除 git checkout/submodule update 步骤中的 `2>/dev/null || true` 错误掩码

## 修复逻辑
CI 分析报告指出三个根因：
1. **FoundationDB RPM URL 硬编码 aarch64**（直接导致 CI 失败）→ 替换为 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` + `COPY --from=fdb` 多阶段构建，彻底规避架构依赖
2. **clang 库路径硬编码 aarch64**（会在 FoundationDB 修复后成为新阻塞点）→ 使用 `ARCH=$(uname -m)` 动态获取容器实际架构（x86_64 返回 `x86_64`，aarch64 返回 `aarch64`），拼接为 `${ARCH}-openEuler-linux-gnu` 三元组
3. **git clone --depth 1 与 commit checkout 不兼容**（模式18）→ 移除 `--depth 1` 和 `--shallow-submodules`，使用完整克隆确保历史 commit 可检出

以上修改均已在 `fix/2512` 分支的先前修复提交中完成，当前 Dockerfile 无需额外代码变更。

## 潜在风险
- `meson install` 步骤仍保留 `2>/dev/null || true`（第23行），若 fuse3 构建安装失败可能被静默跳过，但最终镜像会从 yum 安装的 `fuse3-libs` 提供运行时库，影响有限
- 当前 Dockerfile 相比容器验证版本（`b39b6225`）缺少部分 yum 依赖（如 `clang-tools-extra`、`rdma-core-devel`、`numactl-devel`、`python3-devel`、`autoconf`、`automake`、`libtool`）和 cmake 构建参数（如 `-DCMAKE_CXX_FLAGS="-Wno-error"`、`-DFOLLY_CPP_ATOMIC_BUILTIN=TRUE`、`-DBUILD_TESTING=OFF`），这些回归可能在 CI 通过 FoundationDB 步骤后导致新的构建失败，但不在本次 CI 报告范围内