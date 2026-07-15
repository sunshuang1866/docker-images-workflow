# 修复摘要

## 修复的问题
Conan hook `bzip2_source_fix.py` 未激活，导致 `make build-cpp` 时 bzip2 源码下载 403 失败。

## 修改的文件
- `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`: 在 Conan hook 文件创建后添加 `conan config set hooks=bzip2_source_fix` 以显式激活 hook

## 修复逻辑
原 Dockerfile 已包含一个 Conan `pre_source` hook（`/root/.conan/hooks/bzip2_source_fix.py`），该 hook 将 bzip2 的 conandata.yml 中 `sourceware.org` 源站 URL 替换为 `distfiles.macports.org` 镜像。但 Conan 1.x 的 hook 默认不会自动激活——仅将 `.py` 文件放入 hooks 目录是不够的，必须通过 `conan config set hooks=<hook_name>` 或 conan.conf 的 `[hooks]` 节显式启用。因此 CI 构建中 hook 从未被调用，bzip2 仍从 sourceware.org 下载导致 403。

修复通过在 hook 文件创建后添加 `conan config set hooks=bzip2_source_fix`，显式激活该 hook。已从上游 `conan-io/conan-center-index` 仓库（master 分支，`recipes/bzip2/all/conandata.yml`）获取实际文件内容并在内存中验证：正则可以正确匹配 `https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz` 并替换为 `https://distfiles.macports.org/bzip2/bzip2-1.0.8.tar.gz`，匹配成功。

## 潜在风险
- 若 `distfiles.macports.org` 在 CI 网络中也返回 403，则需进一步更换镜像源。当前 hook 仅替换第一个 URL，conandata.yml 中另有两个备用 URL（`mirrors.kernel.org`、`mirrorservice.org`），Conan 的 `tools.get()` 会按序尝试。
- `conan config set hooks=bzip2_source_fix` 在 conan.conf 尚未初始化时可能失败，但 `pip install conan` 后 ~/.conan 目录已存在，`conan config set` 会自动创建/更新 conan.conf，风险较低。