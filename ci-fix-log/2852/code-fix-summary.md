# 修复摘要

## 修复的问题
bzip2 预下载步骤使用了不可达的 `sourceware.org` 源 URL（返回 HTTP 403），与 Conan hook 中已配置的 `mirrors.kernel.org` 镜像源不一致，导致 CI 构建失败。

## 修改的文件
- `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`: 将第 46 行 bzip2 预下载 URL 从 `https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz` 改为 `https://mirrors.kernel.org/sourceware/bzip2/bzip2-1.0.8.tar.gz`

## 修复逻辑
采用分析报告中的方向 1（置信度: 高）。Dockerfile 中有两处引用 bzip2 源 URL：
1. 第 18-39 行（Conan hook `bzip2_source_fix.py`）：已正确将 bzip2 URL 重定向到 `mirrors.kernel.org`
2. 第 43-46 行（预下载步骤）：使用原始 `sourceware.org` URL，绕过 Conan hook 直接下载，导致 CI 环境返回 403

修复将预下载 URL 与 Conan hook 中的镜像 URL 保持一致，消除了逻辑矛盾。

**验证结果**：已从 `https://mirrors.kernel.org/sourceware/bzip2/bzip2-1.0.8.tar.gz` 获取实际文件，SHA256 为 `ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269`，与预下载步骤中硬编码的 hash 值完全一致，HTTP 返回 200。

## 潜在风险
无。URL 仅替换为同一文件的镜像源，SHA256 已通过实际下载验证一致。