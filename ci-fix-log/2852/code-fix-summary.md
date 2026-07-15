# 修复摘要

## 修复的问题
移除 bzip2 源码下载 URL 替换的 conan hook，该 hook 将 `sourceware.org` 替换为 `fossies.org`，但 `fossies.org` 在 CI 环境中同样返回 403，导致 `make build-3rdparty` 阶段 bzip2/1.0.8 源码下载失败。

## 修改的文件
- `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`: 移除 conan hook（`bzip2_source_fix.py`）的创建和注册代码，恢复为与 `24.03-lts-sp2` 一致的简洁版本

## 修复逻辑
CI 分析报告指出根因是 bzip2/1.0.8 在 conan 中心仓库的上游下载 URL 返回 HTTP 403。sp4 的 Dockerfile 中新增了一个 conan hook，试图将 `sourceware.org` 的源 URL 替换为 `fossies.org` 镜像，但该镜像 URL 在 CI 环境中同样返回 403。

经对比发现，已有的 `2.6.0/24.03-lts-sp2` Dockerfile 不包含该 hook，conan 直接使用配方默认的 `sourceware.org` 源地址。从当前运行环境验证，`sourceware.org` 返回 200 OK，可正常下载。

因此移除 sp4 Dockerfile 中新增的 conan hook，恢复使用配方原始下载 URL，与 sp2 版本保持一致。这样 conan 将使用 bzip2 配方中 `conandata.yml` 定义的原始下载地址，该地址在一般网络环境下可正常访问。

## 潜在风险
如果 CI 构建环境的网络策略同时阻断了 `sourceware.org`（而不仅仅是 `fossies.org`），则该修复无法解决问题。此时真正的根因是 CI 网络限制而非代码问题，需通过 CI 网络配置或使用系统预装的 `bzip2-devel` 替代源码构建来解决。