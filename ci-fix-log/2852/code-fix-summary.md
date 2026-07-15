# 修复摘要

## 修复的问题
Conan 安装 bzip2/1.0.8 时 `source()` 方法下载源码失败：`mirrors.kernel.org` 镜像源返回 HTTP 403 Forbidden。

## 修改的文件
- `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile:33`: 将 bzip2_source_fix 钩子中的替换目标 URL 从 `mirrors.kernel.org/sourceware/bzip2/` 改为 `fossies.org/linux/misc/`

## 修复逻辑
分析报告指出根因是 Conan 的 bzip2 recipe 在 `source()` 方法中尝试从配置的 URL 下载源码，所有已配置的镜像源（`sourceware.org` 和 `mirrors.kernel.org`）均返回 403。Dockerfile 中已有的 `bzip2_source_fix.py` 钩子会将 `sourceware.org` URL 替换为 `mirrors.kernel.org`，但该镜像同样被 CI 环境阻断。

修复将替换目标改为 Fossies 镜像站（`https://fossies.org/linux/misc/bzip2-1.0.8.tar.gz`）。已验证该 URL：
- 返回 HTTP 200
- 文件 SHA256 为 `ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269`，与 Conan recipe 期望的 bzip2 1.0.8 hash 一致

钩子将 Conan recipe 的 `conandata.yml` 中所有 `sourceware.org` URL 替换为 `fossies.org` URL后，Conan 会优先尝试该可用镜像，从而绕过 CI 环境中被阻断的 `mirrors.kernel.org`。

## 潜在风险
无。Fossies 是一个长期稳定的开源软件镜像站，bzip2 1.0.8 自 2019 年发布以来一直可用。若 CI 环境同样阻断 `fossies.org`，则需考虑预下载源码到 Conan 本地缓存的方案（分析报告方向 2），但该方案改动更大且不在当前允许修改的文件范围内。