# 修复摘要

## 修复的问题
无需代码修改。此 PR (#2790) 为纯文档更新（README.md / README.en.md），被 CI appstore 路径校验工具错误拦截，属于 CI 基础设施问题（infra-error）。

## 修改的文件
无。PR 涉及的文件 `README.md` 和 `README.en.md` 本身没有错误，不需要修改。

## 修复逻辑
CI 失败的直接原因是 `eulerpublisher/update/container/app/update.py:273` 中的 appstore 发布规范预检工具对所有 PR diff 文件执行路径校验，要求变更文件位于 `{场景目录}/{镜像名}/{版本号}/{OS版本}/Dockerfile` 等镜像路径下。仓库根目录的 `README.md` 和 `README.en.md` 不符合该模式，被标记为 `[Path Error]`。

实际修复应在 CI 校验工具 `update.py` 中添加对仓库根级文档文件（`README.md`、`README.en.md`）的白名单豁免逻辑，使其允许纯文档类 PR 通过 appstore 路径校验。该文件不在 `pr.changed_files` 允许修改范围内，因此无法在当前修复范围内实施。

## 潜在风险
无。未修改任何源代码，无引入新问题的风险。

### 建议的 CI 端修复方向
在 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑中，对仓库根目录下的 `README.md` 和 `README.en.md` 文件进行跳过处理（例如，在 diff 文件遍历时过滤掉与根级 README 匹配的条目）。