# 修复摘要

## 修复的问题
GitHub Archive tarball 不包含 git submodule（`extra/libkmip`），导致 cmake 配置阶段报错 `does not contain a CMakeLists.txt file`，构建失败。

## 修改的文件
- `Database/percona/8.4.8/24.03-lts-sp3/Dockerfile`:
  - 第 10 行：dnf install 添加 `git` 包
  - 第 16-17 行：将 `wget` 下载 GitHub archive tarball + `tar` 解压 替换为 `git clone --recursive --branch Percona-Server-${VERSION}-${RELEASE}`
  - 删除原第 19 行 `rm -f percona.tar.gz`
  - 第 36 行：dnf remove 添加 `git`（构建后清理）

## 修复逻辑
CI 分析报告指出根因是：Dockerfile 使用 `wget` 从 GitHub Archive（`/archive/refs/tags/...`）下载 percona-server 源码 tarball，但 GitHub 自动生成的归档 tarball 不包含 git submodule 内容。`extra/libkmip` 是 percona-server 仓库的 git 子模块，tar 解压后该目录为空，cmake 执行 `ADD_SUBDIRECTORY` 时找不到 `CMakeLists.txt`。

修复采用分析报告推荐的方向 1：将源码获取方式改为 `git clone --recursive`，该命令会自动拉取所有子模块（包括 `extra/libkmip`、`extra/coredumper`、`storage/rocksdb/rocksdb`），确保 cmake 配置时所有子目录均包含完整的 `CMakeLists.txt`。已从上游 `Percona-Server-8.4.8-8` tag 获取 `.gitmodules` 验证，确认存在 3 个子模块，tag 名格式 `Percona-Server-${VERSION}-${RELEASE}` 展开为 `Percona-Server-8.4.8-8` 正确无误。

## 潜在风险
- `git clone --recursive` 相比 tarball 下载更多数据（完整 git 历史 + 子模块），但 Docker layer 缓存可减轻影响
- `wget` 仍保留在安装列表中（用于下载 gosu），不受此次修改影响