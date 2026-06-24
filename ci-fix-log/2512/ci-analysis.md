# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式10（部分关联）| 主要诊断症状为新模式
- 新模式标题: 架构路径硬编码
- 新模式症状关键词: aarch64, x86_64, foundationdb-clients, el9, RPM architecture mismatch, BUILDARCH, TARGETARCH

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
------
ERROR: failed to solve: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
Dockerfile:22-24
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB clients RPM 下载 URL 硬编码了 `aarch64` 架构标识（`foundationdb-clients-7.3.77-1.el9.**aarch64**.rpm`），而当前 CI 构建在 `x86_64` 宿主机上运行（日志中 Rust 安装为 `x86_64-unknown-linux-gnu`，Fuse 构建 `Host machine cpu family: x86_64`），导致架构不匹配、依赖解析失败。

### 与 PR 变更的关联
PR #2512 新增了完整的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行新代码）。该 Dockerfile 由 AI agent 生成，全程未考虑多架构适配——不仅 FoundationDB RPM URL 硬编码了 `aarch64`，后续步骤中的 clang 库符号链接路径也硬编码了 `aarch64-openEuler-linux-gnu`：

```
ln -sf /usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/libclang_rt.builtins.a \
      /usr/lib64/clang/17/lib/linux/libclang_rt.builtins-aarch64.a
```

这些硬编码的 `aarch64` 路径同样会在 x86_64 构建中失败（但当前 CI 在 FoundationDB 步骤即已终止，未执行到该步）。

**额外注意**：Dockerfile 中还存在 `git clone --depth 1` + `git checkout ${VERSION}`（commit hash）的不兼容模式（匹配**模式18**），以及 `2>/dev/null || true` 静默掩盖错误的陷阱。这些在当前 CI 运行中未被触发，但属于同一 Dockerfile 中的隐患。

## 修复方向

### 方向 1: 使用 BuildKit 架构变量动态选择 RPM（置信度: 高）
在 Dockerfile 中声明 `ARG TARGETARCH`（BuildKit 内置变量，值为 `amd64` 或 `arm64`），将 FoundationDB RPM URL 中的 `aarch64` 替换为基于 `TARGETARCH` 的条件映射：`amd64` → `x86_64`，`arm64` → `aarch64`。同时将 clang 库路径中的 `aarch64-openEuler-linux-gnu` 同步替换为对应架构三元组。

### 方向 2: 放弃 RPM 安装，改用 FoundationDB 官方 Docker 多阶段构建（置信度: 中）
参考**模式16**（RPM 停止发布时的多阶段构建绕过方案），从 `foundationdb/foundationdb:7.3.77` 镜像中 `COPY --from` 提取所需二进制文件，彻底规避 RPM 架构匹配问题。

## 需要进一步确认的点
1. FoundationDB 7.3.77 `.el9.x86_64.rpm` 在 openEuler 24.03-LTS-SP3 上的实际依赖兼容性（即使架构匹配，`.el9` RPM 的 glibc 版本要求也可能与 openEuler 不兼容）——需在 live container 中验证。
2. `git clone --depth 1` + commit hash checkout 问题（模式18）：即使修复了 FoundationDB 架构问题，浅克隆也无法 checkout 到 `22fca04` 这个历史 commit。需先 `git fetch origin ${VERSION}` 再 checkout，或去掉 `--depth 1`。
3. Dockerfile 中 yum install 安装的 `clang-tools-extra`、`gmock-devel`、`gtest-devel`、`libdwarf-devel`、`gperftools-devel` 在此次 CI 运行中安装成功（日志 `#7 DONE 332.7s Complete!`），但 live container 验证后需确认这些包在 openEuler 24.03-LTS-SP3 上确实可用且版本满足 3FS 构建要求。

## 修复验证要求
code-fixer 在提交修复前，必须对 `x86_64` 和 `aarch64` 两个架构分别执行以下验证：
1. 确认 FoundationDB 对应架构 RPM 可在 openEuler 24.03-LTS-SP3 容器中成功 `rpm -ivh`（依赖完全满足）。
2. 若改用多阶段构建（方向2），确认从 `foundationdb/foundationdb:7.3.77` 镜像 COPY 的二进制在 openEuler 容器中可正常执行。
3. 修复 `git clone --depth 1` + commit hash checkout 后，确认 `git -C /tmp/3fs log -1 --format=%H` 输出的 commit hash 前 7 位匹配 `22fca04`。
