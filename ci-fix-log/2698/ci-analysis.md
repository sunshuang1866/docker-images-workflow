# CI 失败分析报告

## 基本信息
- PR: #2698 — Feat: add percona 8.4.8 docker image on openEuler 24.03-LTS-SP3
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Git子模块缺失
- 新模式症状关键词: ADD_SUBDIRECTORY, does not contain a CMakeLists.txt, extra/libkmip, git submodule, GitHub archive tarball

## 根因分析

### 直接错误
```
#8 1044.3 2026-06-22 13:51:42 (10.3 MB/s) - Read error at byte 422235062 (Connection timed out).Retrying.

#8 1467.5 CMake Error at CMakeLists.txt:2242 (ADD_SUBDIRECTORY):
#8 1467.5   The source directory
#8 1467.5
#8 1467.5     /percona/extra/libkmip
#8 1467.5
#8 1467.5   does not contain a CMakeLists.txt file.

#8 1474.9 -- Configuring incomplete, errors occurred!
```

### 根因定位
- 失败位置: `Database/percona/8.4.8/24.03-lts-sp3/Dockerfile:16-17`（wget 下载源码 + tar 解压步骤）
- 失败原因: Dockerfile 使用 `wget` 从 GitHub Archive（`/archive/refs/tags/...`）下载 percona-server 源码 tarball，但 GitHub 自动生成的归档 tarball **不包含 git submodule 内容**。`extra/libkmip` 是 percona-server 仓库的 git 子模块，tar 解压后该目录为空（仅含 `.gitmodules` 引用），cmake 在 `CMakeLists.txt:2242` 执行 `ADD_SUBDIRECTORY` 时找不到 `CMakeLists.txt`，导致配置阶段失败。

### 与 PR 变更的关联
PR 新增了 `Database/percona/8.4.8/24.03-lts-sp3/Dockerfile`，其中源码下载方式选择了 `wget` 下载 GitHub archive tarball。该方式无法获取 git submodule 的内容，是本次失败的**直接原因**。同时日志中出现了 `wget` 下载阶段 `Read error at byte 422235062 (Connection timed out)` 的超时重试记录，即使下载完成，大文件下载的网络不稳定性也可能导致 tarball 不完整，加剧了问题。

## 修复方向

### 方向 1（置信度: 高）
将源码获取方式从 `wget` 下载 GitHub archive tarball 改为 `git clone --recursive`。`git clone --recursive` 会自动拉取所有子模块（包括 `extra/libkmip`），确保 cmake 配置时所需的所有子目录均包含完整的 `CMakeLists.txt`。

需注意：Dockerfile 中需安装 `git` 包，且 `git clone` 时应指定 `--branch` 或直接 checkout 到 `Percona-Server-${VERSION}-${RELEASE}` tag（避免下载 tarball 时 URL 中 tag 名与 VERSION/RELEASE 变量的拼接逻辑问题）。

### 方向 2（置信度: 中）
如果必须使用 tarball 方式（例如构建环境网络限制不允许 git clone），则需要在 Dockerfile 中手动处理 `libkmip` 子模块：在解压后、cmake 前，额外下载 `libkmip` 子模块的源码并放入 `/percona/extra/libkmip/` 目录。但此方案维护成本高，不推荐。

## 需要进一步确认的点
1. **确认子模块清单**：除 `extra/libkmip` 外，percona-server Percona-Server-8.4.8-8 是否还有其他 `extra/` 下的 git submodule 会被 `ADD_SUBDIRECTORY` 引用。验证方式：查看上游仓库 `.gitmodules` 文件，确认所有子模块路径。
2. **确认 tag 名格式**：验证 `Percona-Server-${VERSION}-${RELEASE}` 展开为 `Percona-Server-8.4.8-8` 是否确实是上游仓库的正确 tag 名。
3. **确认 git 包的可用性**：确认 `git` 包在 openEuler 24.03-LTS-SP3 的 dnf 仓库中可直接安装（`dnf install -y git`），无需额外配置。

## 修复验证要求
- code-fixer 修改 Dockerfile 后，必须验证 `git clone --recursive` 能完整拉取 percona-server 及所有子模块，且 cmake 配置阶段不再出现 `extra/libkmip` 缺少 `CMakeLists.txt` 的错误。
- 若采用方向1，需验证 `git clone --recursive` 后的目录结构与当前 tarball 解压结构一致（即 `--strip-components=1` 等价替换为 clone 到 `/percona` 目录），确保后续 `cmake -S /percona -B /percona/build` 路径正确。
