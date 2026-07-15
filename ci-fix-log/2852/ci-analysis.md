# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: sourceware.org 403
- 新模式症状关键词: sourceware.org, 403 Forbidden, curl: (22), bzip2, conan

## 根因分析

### 直接错误
```
#13 [builder 4/5] RUN mkdir -p /root/.conan/data/bzip2/1.0.8/_/_/source &&     curl -fsSL --retry 3 --retry-delay 5       -o /root/.conan/data/bzip2/1.0.8/_/_/source/bzip2-1.0.8.tar.gz       https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz
#13 1.026 curl: (22) The requested URL returned error: 403
#13 ERROR: process "/bin/sh -c mkdir -p /root/.conan/data/bzip2/1.0.8/_/_/source &&     curl -fsSL --retry 3 --retry-delay 5       -o /root/.conan/data/bzip2/1.0.8/_/_/source/bzip2-1.0.8.tar.gz       https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz" did not complete successfully: exit code: 22
------
Dockerfile:42
```

### 根因定位
- 失败位置: `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile:42`（实际构建文件，已与 PR diff 产生差异）
- 失败原因: Dockerfile 中显式 `curl` 预下载 bzip2-1.0.8 源码包时，`https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz` 返回 HTTP 403 Forbidden，导致 Docker 构建在 builder 阶段第 4 步失败。

### 与 PR 变更的关联
PR 新增了 milvus 2.6.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile。milvus 的 C++ 构建依赖 bzip2（通过 conan 管理）。CI 首次构建失败后，已有人为 Dockerfile 增加了两处 workaround：① conan hook（step #12）将 conandata.yml 中的 bzip2 URL 替换为 distfiles.macports.org 镜像；② 新增补 pre-download RUN 步骤（step #13）试图提前将 bzip2 缓存到 `/root/.conan/data/`。但 step #13 中显式 curl 仍使用了原始的 `sourceware.org` URL（而非 hook 中的镜像 URL），导致预下载步骤本身因 403 而失败。**PR 变更直接触发了此失败。**

---

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 第 42-45 行（bzip2 预下载 RUN 指令）中的 URL 从 `https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz` 替换为已验证可达的镜像 URL（如 `https://distfiles.macports.org/bzip2/bzip2-1.0.8.tar.gz`），与同文件中 conan hook（step #12）使用的镜像保持一致。

### 方向 2（置信度: 中）
如已验证镜像 URL 同样不可达，可改为先尝试 curl 原始 URL，失败时自动 fallback 到镜像 URL：
```sh
curl -fsSL --retry 3 https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz -o ... ||
curl -fsSL --retry 3 https://distfiles.macports.org/bzip2/bzip2-1.0.8.tar.gz -o ...
```

### 方向 3（置信度: 低，备选）
移除显式的预下载 RUN 步骤（step #13），仅依赖 step #12 中已创建的 conan hook 在 conan 解析 bzip2 依赖时自动 patch URL。风险：若 conan hook 因路径或权限问题未生效，构建仍会失败。

---

## 需要进一步确认的点

1. **Dockerfile 实际内容与 diff 不一致**：PR diff 中 Dockerfile 仅 53 行，不包含 bzip2 预下载步骤，但 CI 构建日志显示该步骤位于 Dockerfile:42。需确认当前分支上 Dockerfile 的实际完整内容是否为修正后的版本，以及 conan hook 与预下载步骤是否在同一个 RUN 中还是分开的。
2. **sourceware.org 403 的时效性**：sourceware.org 对 bzip2 旧版本返回 403 是临时性限制还是永久性政策。如果是一致性问题，需考虑将所有 conan 依赖中指向 sourceware.org 的 URL 一并替换。
3. **镜像 URL 可用性验证**：`https://distfiles.macports.org/bzip2/bzip2-1.0.8.tar.gz` 是否在 CI 构建环境中确实可达，建议在修复前单独 curl 测试。

## 修复验证要求
code-fixer 必须在修复后确认：
1. `curl -fsSL --retry 3` 测试新的镜像 URL 在 CI 同网段环境中可达（返回 200 且文件为有效 gzip）。
2. Dockerfile 中 bzip2 预下载 URL 与同文件中 conan hook（step #12）的替换 URL 一致（均为 `distfiles.macports.org`）。
3. 若选择方向 3（移除预下载步骤），需验证 conan hook 在实际 build-cpp 过程中确实被调用并成功 patch 了 conandata.yml。
