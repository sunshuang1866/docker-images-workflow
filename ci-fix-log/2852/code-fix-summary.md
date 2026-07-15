# 修复摘要

## 修复的问题
Conan 包管理器在下载 bzip2/1.0.8 源码时，comandata.yml 中指向 `sourceware.org` 的下载 URL 在 CI 环境中返回 HTTP 403 Forbidden，导致 `conan install` 失败，进而 `make build-cpp` 整个构建阶段中断。

## 修改的文件
- `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`: 在安装 conan 1.61.0 的 RUN 层中添加了 conan hook 脚本创建步骤。该 hook 在 `pre_source` 阶段将 bzip2/1.0.8 的源下载 URL 从 `https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz` 替换为 `https://distfiles.macports.org/bzip2/bzip2-1.0.8.tar.gz`（MacPorts 镜像，经测试可正常访问且 sha256 一致）。

## 修复逻辑
修复采用了 conan hook 机制——在 `~/.conan/hooks/` 目录下创建一个 `bzip2_source_fix.py` 文件，其中定义了 `pre_source` 钩子函数。当 conan 执行到 `source()` 步骤前，该 hook 会被自动调用，打开 bzip2 recipe 的 conandata.yml 文件并用字符串替换将不可达的 sourceware.org URL 改为可用的 MacPorts 镜像 URL。

**验证情况**: 已从 conan-center-index 上游仓库 (`conan-io/conan-center-index`, master 分支) 获取 `recipes/bzip2/all/conandata.yml` 文件，确认源文件中确实包含 `https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz`，字符串替换匹配成功。MacPorts 镜像 `https://distfiles.macports.org/bzip2/bzip2-1.0.8.tar.gz` 经 Python urllib 测试可正常返回 200 和正确文件内容（810029 bytes）。

## 潜在风险
- MacPorts 镜像的长期可用性依赖于 macports.org 的维护策略，若该镜像未来也失效，需更换其他可用镜像
- Hook 在每次 conan `source()` 调用时都会执行，但对非 bzip2 包会快速返回（仅检查 reference.name），性能影响可忽略
- 若 CI 环境中 `sourceware.org` 未来恢复访问，hook 将其重定向到 MacPorts 镜像，功能上无差异（同一文件，sha256 一致）