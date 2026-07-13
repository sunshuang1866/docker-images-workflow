# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范校验）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对 PR 中所有变更文件执行路径规范校验。根目录下 `README.md` 和 `README.en.md` 不匹配 appstore 发布要求的镜像目录路径模式（期望格式为 `{image-version}/{os-version}/Dockerfile` 等），因此被标记为 `Path Error`。

### 与 PR 变更的关联
PR 仅修改了根目录下的两个纯文档文件 `README.md` 和 `README.en.md`（更新可用基础镜像 tag 列表），未涉及任何 docker 镜像构建文件。CI 的 appstore 路径校验对所有变更文件一视同仁地执行检查，导致这两个文档文件因不属于任何镜像目录而触发了路径校验失败。这是 CI 校验范围过宽的问题——纯文档 PR 不应受镜像发布规范约束。

## 修复方向

### 方向 1（置信度: 高）
CI 检查脚本 `update.py` 需要在遍历 PR 变更文件时，排除根目录级文档文件（如 `README.md`、`README.en.md`、`CONTRIBUTING.md` 等非镜像目录下的文件），使其仅对镜像目录内的文件执行 appstore 路径规范校验。

### 方向 2（置信度: 中）
若 CI 脚本不具备排除逻辑的修改条件，可考虑将根目录 README 文件注册到特定元数据或白名单中，使路径校验规则能正确识别它们为非镜像文件，但此方向仅为绕过方案，不如方向 1 从根本上解决问题。

## 需要进一步确认的点
- CI 检查脚本 `eulerpublisher/update/container/app/update.py` 中文件遍历和路径校验逻辑的具体实现（当前日志中不可见），以确认添加文件过滤/排除逻辑的最佳位置。
- 确认该仓库中还有哪些根目录级文件（如 `CONTRIBUTING.md`、`LICENSE`、`.gitignore` 等）同样会触发此类错误，以便一次性全面排除。
- 确认 `eulerpublisher` 仓库是否有对应的 PR 修复流程（该脚本不在本仓库中管理）。
