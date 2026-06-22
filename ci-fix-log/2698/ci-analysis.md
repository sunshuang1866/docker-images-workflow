# CI 失败分析报告

## 基本信息
- PR: #2698 — Feat: add percona 8.4.8 docker image on openEuler 24.03-LTS-SP3
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: GitHub归档缺失子模块
- 新模式症状关键词: CMakeLists.txt, does not contain, extra/libkmip, ADD_SUBDIRECTORY, percona-server, archive/refs/tags, git submodule

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
#8 ERROR: process "/bin/sh -c dnf install -y ... && cmake -S /percona -B /percona/build ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Database/percona/8.4.8/24.03-lts-sp3/Dockerfile:21`（cmake 配置步骤）
- 失败原因: 通过 `wget` 从 GitHub `archive/refs/tags/` 下载的 percona-server 源码 tarball 不包含 git submodule 内容，`extra/libkmip` 目录为空（无 CMakeLists.txt），导致 cmake 的 `ADD_SUBDIRECTORY` 调用失败。

### 与 PR 变更的关联
本次 PR 新增的 Dockerfile（`Database/percona/8.4.8/24.03-lts-sp3/Dockerfile`）在 `RUN` 指令中使用了 GitHub 自动生成归档 tarball 作为源码获取方式：
```
wget -O percona.tar.gz "https://github.com/percona/percona-server/archive/refs/tags/Percona-Server-${VERSION}-${RELEASE}.tar.gz"
```
GitHub 的 `archive/refs/tags/` 接口生成的 tarball **不包含** git submodule 内容。percona-server 仓库中 `extra/libkmip` 是一个 git submodule，在 tarball 中该目录存在但为空，导致 cmake 配置阶段报错。该失败完全由本次 PR 引入。

附注：日志中同时出现了下载超时重试（`Read error at byte 422235062 (Connection timed out).Retrying.`），但后续 cmake 已成功启动执行，说明重试后下载完成，超时非根本原因。

## 修复方向

### 方向 1（置信度: 高）
将源码获取方式从下载 GitHub release tarball 改为 `git clone --recurse-submodules`，确保 submodule 内容被完整拉取。克隆指定 tag 后进入源码目录进行 cmake 构建，替代当前的 `wget + tar + cmake` 流程。

### 方向 2（置信度: 中）
在 cmake 参数中添加 `-DWITH_KMIP=OFF`（或 percona-server 提供的等效 cmake option），跳过 libkmip 子目录的构建。需先确认 percona-server 8.4.8 的顶层 `CMakeLists.txt` 是否支持该选项，以及 `extra/libkmip` 的 `ADD_SUBDIRECTORY` 是否有对应的条件控制。

## 需要进一步确认的点
- percona-server 仓库中 `extra/libkmip` 确认为 git submodule（可在 percona-server 仓库中查看 `.gitmodules` 文件确认）
- 如果选择方向 2，需确认 percona-server 的 cmake 构建系统是否提供禁用 libkmip 的选项（如 `-DWITH_KMIP=OFF`），以及禁用后是否影响 percona-server 的目标功能

## 修复验证要求
若修复方向涉及从 git clone 获取源码替代 tarball，code-fixer 必须验证：
1. `git clone --recurse-submodules --branch Percona-Server-8.4.8-8 https://github.com/percona/percona-server.git /percona` 能成功拉取包括 `extra/libkmip` 在内的所有 submodule
2. 克隆后的 `/percona/extra/libkmip/CMakeLists.txt` 文件存在
3. cmake 配置步骤不再报 `does not contain a CMakeLists.txt file` 错误
