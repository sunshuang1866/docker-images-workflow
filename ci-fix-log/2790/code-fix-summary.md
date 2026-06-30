# 修复摘要

## 修复的问题
CI appstore 发布规范预检错误地拦截了纯文档类 PR #2790。`eulerpublisher/update/container/app/update.py:273` 的路径校验逻辑将根目录的 `README.en.md` 和 `README.md` 按应用镜像发布规范进行检查，其中 `README.en.md` 不在 appstore 认可的文件清单内，`README.md` 则因不匹配任何应用镜像目录模式而级联失败。

## 修改的文件
无。此为 CI 基础设施问题，`README.md` 和 `README.en.md` 两个文件内容本身正确且无违规之处，无需修改。

## 修复逻辑
此 CI 失败属于 **infra-error**（CI 基础设施问题）：

1. PR #2790 仅修改了根目录的两个文档文件（`README.md`、`README.en.md`），不涉及任何 Dockerfile、meta.yml、image-info.yml 等应用镜像构建/发布文件。
2. CI 中的 `eulerpublisher` 工具（位于外部仓库 `eulerpublisher/update/container/app/update.py`，不在当前源码仓库内）的 appstore 发布规范预检逻辑将所有变更文件都纳入校验范围，未区分纯文档类 PR 和应用镜像发布 PR。
3. `README.en.md` 不在 appstore 发布规范认可的文件清单内，直接触发 Path Error。
4. 两个文件均位于仓库根目录，不匹配任何应用镜像场景目录模式（如 `AI/nginx/README.md`），因此路径校验必然失败。
5. 根因修复需要在 `eulerpublisher` 外部工具的 CI 校验逻辑中做修改（如排除根目录纯文档文件、或在 trigger 层面排除纯文档类 PR），当前源码仓库内的改动无法解决此问题。

## 潜在风险
无。未对源码仓库做任何修改，不存在引入新问题的风险。