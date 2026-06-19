# 修复摘要

## 修复的问题
Dockerfile 中 git clone 构造的分支名 `CMAQv5.5.2Oct2024_2Oct2024` 在 USEPA/CMAQ 上游仓库中不存在，导致构建失败。

## 修改的文件
- `HPC/cmaq/5.5.2Oct2024/24.03-lts-sp3/Dockerfile:60`: 将 git clone 的分支名从 `CMAQv${VERSION}_2Oct2024`（展开为 `CMAQv5.5.2Oct2024_2Oct2024`）改为已验证存在的上游 tag `CMAQv5.5_2Oct2024`

## 修复逻辑
根因：VERSION 变量值为 `5.5.2Oct2024`，已包含日期后缀 `2Oct2024`，而 git clone 模板又追加了 `_2Oct2024`，导致日期重复拼接，构造出的 `CMAQv5.5.2Oct2024_2Oct2024` 在上游不存在。

上游 USEPA/CMAQ 仓库中对应 5.5 Oct 2024 版本的唯一引用是 tag `CMAQv5.5_2Oct2024`（已通过 `git ls-remote` 验证存在，commit f62e51181b5d4ff92df3a1fe5e711b91a1101309）。不存在名为 `CMAQv5.5.2Oct2024` 的分支或 tag。

将 git clone 的分支参数直接改为已验证的上游 tag `CMAQv5.5_2Oct2024`。

## 潜在风险
- VERSION ARG（`5.5.2Oct2024`）在 Dockerfile 中未在其他地方使用，因此将其从 git clone 命令中移除不影响其他构建步骤。
- 使用 tag（而非 branch）进行 shallow clone（`--depth 1`）与原有分支克隆行为一致，因为 git clone -b 同时支持 branch 和 tag。