# 修复摘要

## 修复的问题
`Database/image-list.yml` 缺少 percona 镜像根目录注册条目，导致多场景校验失败（`Cloud/` 和 `Database/` 同时包含 percona 文件时，CI 的 `parse_image_prefix` 要求所有涉及场景的 image-list.yml 都完整注册）。

## 修改的文件
- `Database/image-list.yml`: 添加 `percona: percona` 条目并修复末尾缺少换行符的问题

## 修复逻辑
CI 失败分析报告指出 root cause 是 `Database/image-list.yml` 缺少 `percona: percona` 条目。原始 PR b46fbb1d 仅在 `Cloud/` 目录下添加了 percona 文件并更新了 `Cloud/image-list.yml`，后续提交将 percona 复制到 `Database/` 目录下但遗漏了更新 `Database/image-list.yml`，导致 CI 多场景校验流程中 `parse_image_prefix` 无法在 `Database/image-list.yml` 中找到 percona 的根目录映射。本次修复在 `Database/image-list.yml` 末尾添加 `percona: percona` 条目，使两个场景的 image-list.yml 均包含完整的 percona 注册。

## 潜在风险
无。该修改与 `Cloud/image-list.yml` 中已有的 percona 条目完全一致，符合项目中所有其他镜像的场景注册模式。