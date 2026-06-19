# 修复摘要

## 修复的问题
CI 构建失败：Dockerfile 中 `ARG VERSION=5.4.1` 指定的 Redis 版本不存在（GitHub 返回 404），导致源码下载失败。已将此无效版本号修正为实际存在且与 Dockerfile 模板兼容的版本 `8.6.4`。

## 修改的文件
- `Database/redis/5.4.1/24.03-lts-sp3/Dockerfile`: 修改 `ARG VERSION=5.4.1` 为 `ARG VERSION=8.6.4`
- `Database/redis/meta.yml`: 将 tag 条目从 `5.4.1-oe2403sp3` 更新为 `8.6.4-oe2403sp3`（路径 `5.4.1/24.03-lts-sp3/Dockerfile` 保持不变，因为该文件仍位于原目录）
- `Database/redis/README.md`: 更新 tag 描述行：`5.4.1-oe2403sp3` → `8.6.4-oe2403sp3`，版本描述 `redis 5.4.1` → `redis 8.6.4`
- `Database/redis/doc/image-info.yml`: 同样更新 tag 描述行

## 修复逻辑

1. **根因确认**：`5.4.1` 不是合法的 Redis 官方发布版本。通过 GitHub API (`refs/tags`) 和 `releases/tag/5.4.1`（返回 404）验证，Redis 仓库中不存在该 tag。5.x 系列的实际版本为 5.0.0–5.0.14。

2. **版本选择**：CI 分析建议使用最新 5.x 版本（5.0.14），但经交叉验证发现：
   - Redis 5.0.14 不含 `deps/fast_float`（该目录在 8.6.4 及更低 8.x 中存在，在 8.8.0 中被移除）
   - Redis 5.0.14 不使用 `createBoolConfig` 配置函数（该函数在 Redis 7.0 重构中引入）
   - 因此 5.0.14 无法通过该 Dockerfile 构建
   - 选择 `8.6.4`：它是 8.8.0 之前（`fast_float` 被移除前）的最新稳定版本，与 Dockerfile 模板完全兼容

3. **验证**：已通过 `wget --spider` 确认 `https://github.com/redis/redis/archive/refs/tags/8.6.4.tar.gz` 返回 HTTP 200；已通过 GitHub API 确认 8.6.4 tag 存在，且 `deps/fast_float` 目录仍存在于该版本中。

## 潜在风险
- 目录名 `Database/redis/5.4.1/` 与 Dockerfile 内的 `VERSION=8.6.4` 不一致。这是自动升级系统生成错误版本号的遗留问题——它创建了包含 8.x Dockerfile 模板的目录，却用了不存在的 `5.4.1` 版本号。`meta.yml` 中的路径仍然指向实际的文件位置。未来可通过将目录重命名为 `8.6.4/` 并将此条目移至 `Database/redis/8.6.4/24.03-lts-sp3/` 来彻底解决，这需要一个单独的清理 PR。
- `README.md` 和 `image-info.yml` 中的 URL 路径仍包含 `5.4.1`（指向文件的实际位置），但它们仍然有效，因为文件确实位于该路径。