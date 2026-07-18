# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题：appstore 发布规范预检（`update.py`）对仅含根级文档变更（`README.md`）的 PR 不应触发镜像路径校验。

## 修改的文件
无（CI 基础设施问题，不在 `README.md` 代码修改范围内）

## 修复逻辑
CI 失败的直接错误为 `update.py:273` 的 appstore 发布规范校验将根目录的 `README.md` 判定为不符合镜像路径规范（期望格式为 `{category}/{image}/{version}/{os-version}/Dockerfile`）。PR #2790 仅更新了 `README.md` 中的镜像 tag 条目（`25.09`、`24.03-lts-sp3`、`24.03-lts-sp2`），是纯文档变更，不存在代码缺陷。

根因是 CI 流水线未对纯文档 PR 跳过 appstore 校验步骤，需要在 CI 流水线/Jenkins job 配置层面解决（例如在 `update.py` 中增加对根级文档文件的过滤逻辑，或为文档类 PR 设置免检机制）。`README.md` 文件内容本身没有问题，强制修改该文件无法解决 CI 失败，只会引入不必要的变更。

## 潜在风险
无（未做任何代码修改）