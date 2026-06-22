# 修复摘要

## 修复的问题
CI 预检工具在 `Database/percona/README.md` 上触发 `parse_image_prefix` 的 ValueError：`Database/image-list.yml` 缺少 percona 镜像根目录条目，同时 `Cloud/image-list.yml` 中的残留 percona 条目触发了不必要的多场景（multi-scene）校验路径。

## 修改的文件
- `Database/image-list.yml:19`: 新增 `percona: percona` 条目（与已有条目格式一致）
- `Cloud/image-list.yml:34`: 删除残留的 `percona: percona` 条目

## 修复逻辑
根据 CI 分析报告和 git 历史，PR #2698 初始添加 percona 到 Cloud 目录，后经 commit `757d005f`（"Fix percona category: move from Cloud to Database"）将 percona 从 Cloud 迁移到 Database。该 commit 通过 `git mv` 重命名文件并更新了两个 `image-list.yml`，但分支合并后 `Database/image-list.yml` 的变更丢失（percona 条目缺失），而 `Cloud/image-list.yml` 的 percona 条目被恢复。这导致 CI 检测到 Cloud 和 Database 两个场景下均存在 percona 文件，触发 multi-scene 严格校验，进而因 `Database/image-list.yml` 缺少 percona 条目而报错。

修复方案：在 `Database/image-list.yml` 末尾添加 `percona: percona`（与其他条目格式一致），并从 `Cloud/image-list.yml` 中删除残留的 `percona: percona` 条目。这与 commit `757d005f` 的预期行为一致：percona 归属 Database 场景。

## 潜在风险
- `Database/image-list.yml` 不在原始 PR 的 `pr.changed_files` 列表中，但 CI 错误明确要求修改此文件。修改格式与所有已有条目一致（`镜像名: 镜像名`），无格式兼容性风险。
- `Cloud/image-list.yml` 删除了 percona 条目，这与 commit `757d005f` 的迁移意图一致。若 Cloud 场景未来需要 percona，需重新添加并同步 `Database/image-list.yml`。