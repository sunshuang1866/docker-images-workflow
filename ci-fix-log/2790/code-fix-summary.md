# 修复摘要

## 修复的问题
CI 基础设施误报：appstore 发布规范预检工具对纯文档 PR（仅修改根级 README.md / README.en.md）报路径错误，实际 README 文件内容正确，无需代码修改。

## 修改的文件
无。README.en.md 和 README.md 的内容更新（新增 Tags 条目）是正确的，不属于镜像发布路径下的文件变更，CI 预检工具不应将其纳入 appstore 发布规范检查范围。

## 修复逻辑
分析报告明确指出这是 CI appstore 预检工具（`eulerpublisher/update/container/app/update.py`）的**误报**，属于 infra-error 类型。PR 仅包含两个根级文档文件的变化，无任何 Dockerfile、meta.yml 或 image-info.yml 等镜像发布相关文件变更。根本解决方案应在 CI 流水线中添加对纯文档 PR 的跳过判断逻辑（当 PR 仅修改根级 `.md` 文件时跳过 appstore 发布规范检查），但该文件不在本 PR 的允许修改范围内。README 文件本身的内容和位置均符合仓库规范，强行将其移入子目录或修改内容来绕过 CI 检查是不合理的。建议由管理员手动豁免该检查后合并。

## 潜在风险
无。未对任何代码文件进行修改。