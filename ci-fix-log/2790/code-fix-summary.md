# 修复摘要

## 修复的问题
无需代码修改。CI 失败根因是 `eulerpublisher/update/container/app/update.py`（CI appstore 发布预检工具）的路径校验逻辑不兼容仓库根目录文件的变更，属于 CI 基础设施缺陷，而非 PR 内容错误。

## 修改的文件
- 无。`README.md` 的内容合法正确，无需修改。

## 修复逻辑
CI 分析报告指出：
- PR #2790 仅修改了仓库根目录 `README.md`，内容为更新支持的镜像 Tags 列表，属于合法文档更新。
- CI 失败的直接原因是 appstore 预检工具期望路径格式为 `/README.md`，且该工具设计上预期 PR 仅包含应用镜像子目录下的文件变更，对根目录文件变更未做兼容处理。
- 真正需要修复的是 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑（对根目录文件做白名单豁免），但该文件不在 PR 允许修改的范围内（`pr.changed_files` = `['README.md']`）。
- `README.md` 内容本身无任何问题，强行修改 README.md 无法解决 CI 失败。

## 潜在风险
无。`README.md` 无需改动，不存在代码层面的风险。建议由 CI 维护团队修复 `update.py` 中的路径校验逻辑，使根目录文件变更不被误判为违规。