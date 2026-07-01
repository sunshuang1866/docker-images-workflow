# 修复摘要

## 修复的问题
CI 基础设施问题：appstore 发布规范预检工具 (`update.py`) 错误地对纯文档 PR 执行路径校验，将根目录的 `README.en.md` 和 `README.md` 判定为不符合 `{category}/{image}/{version}/{os-version}/Dockerfile` 路径规范。无需代码修改。

## 修改的文件
无

## 修复逻辑
PR #2790 仅修改了仓库根目录下的 `README.en.md` 和 `README.md`（更新支持的镜像 Tags 条目），属于纯文档维护工作，不涉及任何 Dockerfile 或镜像构建文件的变更。CI 流水线中的 appstore 发布规范预检步骤对 diff 文件列表进行路径校验时，发现变更文件不满足应用镜像发布所需的层级结构而报错。这是 CI 流水线对文档类变更的预期行为——该检查项设计用于验证应用镜像目录结构，不应应用于根目录文档文件。

分析报告确认此为纯文档 PR（置信度: 高），建议直接忽略 CI 失败。`README.en.md` 和 `README.md` 的内容本身正确无误，无需对源码进行任何修改。

## 潜在风险
无