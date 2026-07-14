# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），是 appstore 发布规范预检工具对根目录纯文档变更的过度拦截，与 PR 的 README 文档更新内容无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`，根因是 CI 预检工具 `eulerpublisher/update/container/app/update.py:273` 对根目录文件 `README.md` 和 `README.en.md` 执行了 appstore 镜像发布路径校验，而这两个文件不属于应用镜像目录结构，不应受该规范约束。修复方向指向修改 CI 预检工具添加根目录文件白名单/免检逻辑，但该工具不在本 PR 的变更文件列表中，也不在当前仓库内。PR 仅修改了两个 README 文档，内容本身无问题，应通过 CI 旁路合并或其他渠道处理。

## 潜在风险
无