# 修复摘要

## 修复的问题
无需代码修改。CI 失败是 `eulerpublisher` appstore 规范校验工具对根级文档文件 `README.md` 产生的误报（false positive），与 PR 改动本身的正确性无关。

## 修改的文件
无。PR 仅修改了 `README.md`（纯文档修正："可用镜像 Tags" 列表的仓库链接更新），内容本身没有问题，不需要修改。

## 修复逻辑
CI 分析报告明确指出：`eulerpublisher/update/container/app/update.py:273` 的 appstore 发布规范预检工具对根目录下的 `README.md` 执行了镜像路径校验（期望路径 `/README.md` 应为 `{image-name}/{version}/{os-version}/Dockerfile` 格式），这是一个 **CI 基础设施层面的工具缺陷**，而非 PR 代码质量问题。

根级 `README.md` 是仓库级文档文件，不属于任何镜像提交，不应被镜像路径校验规则覆盖。实际的修复应在 CI 工具或流水线层面进行（如：排除根级文档文件的路径校验，或在仅含文档变更的 PR 中跳过 appstore 检查），不在本 PR 的可修改范围内。

## 潜在风险
无。PR 改动仅为 README 文档中的链接更新，内容正确，不影响任何镜像构建、发布或测试逻辑。