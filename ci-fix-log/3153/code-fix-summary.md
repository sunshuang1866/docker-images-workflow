# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error）——appstore 发布预检工具对仓库根目录 `README.md` 的路径校验属于假阳性，无需修改源代码。

## 修改的文件
无

## 修复逻辑
根据 CI 失败分析报告，此次 CI 失败属于 **infra-error**，根本原因是 CI 的 appstore 预检工具（`eulerpublisher/update/container/app/update.py`）将根目录下的 `README.md` 纳入了应用镜像路径规范校验范围，导致误报。PR #3153 的变更仅涉及文档更新（README.md 和 README.en.md 中基础镜像标签列表），内容合法且正确，无需对源代码做任何修改。

修复应在上游 CI 工具仓库（eulerpublisher）中的 `update.py` 添加路径排除规则，使预检工具仅针对应用镜像目录下的文件进行校验，排除仓库根目录及非镜像目录文件。此修复不在当前仓库范围内。

## 潜在风险
无