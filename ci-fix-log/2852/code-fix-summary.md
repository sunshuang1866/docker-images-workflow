# 修复摘要

## 修复的问题
Conan 构建 bzip2/1.0.8 时源下载 URL 返回 403 Forbidden，导致 `make build-3rdparty` 失败。

## 修改的文件
- `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`: 在 `./scripts/install_deps.sh` 与 `make build-cpp` 之间添加 Conan recipe 预下载与 bzip2 源 URL patch 逻辑

## 修复逻辑
此修复对应分析报告中的**方向 1**。

根因是 bzip2/1.0.8 的 Conan recipe 中配置的三个源下载 URL（sourceware.org、mirrors.kernel.org、mirrorservice.org）在 CI 构建环境中均返回 403 Forbidden。

修复分三步走：
1. **预下载 recipe**：在正常构建前，先执行一次 `conan install --build=never` 将所有依赖包的 recipe（包括 bzip2）下载到本地缓存 `~/.conan/data/`，这一步只下载元数据不下载源码，即使无预编译包也允许失败（`|| true`）
2. **Patch 源 URL**：用 `find + sed` 在缓存的 bzip2 conandata.yml 中将所有 `bzip2-1.0.8.tar.gz` 的下载 URL 替换为可用的 macports 镜像 `https://distfiles.macports.org/bzip2/bzip2-1.0.8.tar.gz`
3. **清理缓存**：删除已缓存的 bzip2 source/build 目录，确保后续构建时重新用新 URL 下载源码

已从 upstream conan-center-index master 获取 `recipes/bzip2/all/conandata.yml` 验证，正则 `https://[^"]*bzip2/bzip2-1.0.8.tar.gz` 可匹配所有三个原始 URL。macports 镜像 URL 已验证可达（HTTP 200）。

## 潜在风险
- 若 macports 镜像在 CI 环境中不可达，构建仍会失败。但该镜像为 Apache 社区维护的长期稳定镜像，可靠性高。
- 若 Milvus 未来升级使用 bzip2 其他版本（如 1.0.6），该 patch 不会生效（因 URL 中包含版本号 `1.0.8`），但届时也不会有 403 问题（不同版本 URL 不同）。
- 预下载 (`conan install --build=never`) 步骤虽然标记了 `|| true`，但如果 CI 网络无法连接 JFrog Artifactory，bzip2 recipe 不会缓存，后续 `find` 也找不到文件，构建将以原始 URL 重试。