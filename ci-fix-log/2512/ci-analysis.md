# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨架构RPM硬编码
- 新模式症状关键词: `error: Failed dependencies`, `aarch64.rpm`, `GLIBC_2.17`, `foundationdb-clients`, `el9.aarch64`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
    rpm -ivh /tmp/fdb-clients.rpm && \
    rm -f /tmp/fdb-clients.rpm
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
ERROR: failed to solve: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
```

构建环境确认：
- 日志 `#8` 中 Rustup 检测到 `default host triple is x86_64-unknown-linux-gnu`
- 日志 `#9` 中 Meson 检测到 `Host machine cpu family: x86_64`
- 因此当前 CI 构建为 **x86_64 架构**，但 FoundationDB RPM URL 被硬编码为 `aarch64`

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构字符串，未使用 BuildKit 内置变量 `TARGETARCH` 做架构感知选择。当前 CI job 在 x86_64 环境下运行，无法安装 aarch64 架构 RPM，导致 `rpm -ivh` 依赖解析失败（x86_64 系统无法为 aarch64 RPM 提供 `libm.so.6(GLIBC_2.17)(64bit)` 的跨架构依赖满足）。

### 与 PR 变更的关联
PR 的核心变更是新增 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（全新 69 行文件），该 Dockerfile 的 FoundationDB 安装步骤直接触发了此次构建失败。其余变更（`.agents/` → `.claude/` 目录重命名、`image-list.yml` 加入 3fs 条目）与本次失败无关。

## 潜在后续失败点（本次未触发，但修复后可能暴露）

以下问题在当前 CI 日志中尚未触发（构建在 FoundationDB 步骤提前终止），但历史知识库已记录为此次 PR 的已知问题：

1. **git clone --depth 1 + commit hash checkout 不兼容** (`Dockerfile:27`)：`git -C /tmp/3fs checkout ${VERSION} 2>/dev/null || true` 在浅克隆（`--depth 1`）中无法检出历史 commit `22fca04`，且 `|| true` 静默吞下错误 → 构建会使用错误的源码版本（见 **模式18**）

2. **git submodule update --depth 1** (`Dockerfile:28`)：同上，`git submodule update --init --recursive --depth 1 2>/dev/null || true` 同样存在浅克隆与指定版本不兼容问题

3. **clang 库路径硬编码 aarch64** (`Dockerfile:36-40`)：`ln -sf /usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/...` 路径硬编码 aarch64，在 x86_64 上对应的路径为 `x86_64-openEuler-linux-gnu`，虽被 `2>/dev/null || true` 掩蔽但会导致 clang 内置链接库缺失

4. **boost-foundation 包名可能不存在** (Dockerfile 第二个 `yum install` 中)：历史知识库 **模式10** 标注 `boost-foundation` 在 openEuler 中可能不存在

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 中声明 `ARG TARGETARCH`，利用 BuildKit 内置变量根据目标架构动态选择 FoundationDB RPM URL。FoundationDB 在 GitHub Releases 中分别提供了 x86_64 和 aarch64 架构的 RPM（文件名模式为 `foundationdb-clients-{VERSION}-1.el7.x86_64.rpm` 和 `foundationdb-clients-{VERSION}-1.el9.aarch64.rpm`），需要在 `RUN` 中根据 `TARGETARCH` 值（`amd64`/`arm64`）映射到正确的文件名片段。

### 方向 2（置信度: 高）
同样的架构感知逻辑需要应用到 clang 库路径的 `ln` 命令（`Dockerfile:36-40`）：`/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu` 在 x86_64 下应为 `x86_64-openEuler-linux-gnu`，需根据 `TARGETARCH` 动态选择路径前缀。

### 方向 3（置信度: 中）
修复 git clone 浅克隆与 commit checkout 不兼容问题（模式18）：将 `git checkout ${VERSION} 2>/dev/null || true` 改为先 `git fetch origin ${VERSION}` 再 `git checkout FETCH_HEAD`，或去掉 `--depth 1` 改为完整克隆。

## 需要进一步确认的点

1. **FoundationDB x86_64 RPM 的确切文件名**：需确认 `foundationdb-clients-7.3.77-1.el7.x86_64.rpm` 在 GitHub Releases 中是否存在。Apple FoundationDB 的 GitHub Releases 页面（`https://github.com/apple/foundationdb/releases/tag/7.3.77`）需验证 x86_64 架构 RPM 的实际文件名和 el 版本号（可能是 `el7` 而非 `el9`）。

2. **clang 路径在 x86_64 openEuler 中的确切形式**：需在 openEuler 24.03-LTS-SP3 x86_64 容器中确认 `/usr/lib/clang/17/lib/` 下的实际目录名（可能为 `x86_64-openEuler-linux-gnu` 或 `x86_64-redhat-linux-gnu`）。

3. **boost-foundation 包在 openEuler 24.03-LTS-SP3 中的可用性**：需在目标容器中验证 `yum search boost-foundation` 是否可找到，若不可用需确认替代包名（如 `boost-devel`）。

## 修复验证要求

若修复方向 1 涉及动态选择 RPM URL，code-fixer 必须在修复后分别以 `--platform linux/amd64` 和 `--platform linux/arm64` 启动构建验证，确保两个架构的 FoundationDB RPM 均能正确下载并安装。对于修复方向 3（git fetch + checkout），需确认仓库当前 commit `22fca04` 仍在 `deepseek-ai/3fs` 上游仓库中可访问。
