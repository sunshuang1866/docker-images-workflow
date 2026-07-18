# 修复摘要

## 修复的问题
CI appstore 发布规范预检工具对根目录纯文档文件 `README.md` 误报路径错误，属于 CI 基础设施误报，无需对源码进行修改。

## 修改的文件
无

## 修复逻辑
- CI 失败来自 `eulerpublisher/update/container/app/update.py:273` 的 appstore 发布规范预检，该工具对根目录 `README.md` 执行路径校验时报告"预期路径应为 /README.md"。
- `README.md` 实际位于仓库根目录（即 `/README.md`），路径本身正确，且该文件为纯文档文件，不涉及任何镜像 Dockerfile、meta.yml 或 image-info.yml。
- PR #3153 仅更新了 README 中的基础镜像可用 tag 列表（文档更新），不涉及 appstore 镜像发布，不应被纳入 appstore 规范检查范围。
- 这是 CI 工具配置层面的问题（缺少对根目录纯文档文件的豁免逻辑），属于 CI 基础设施误报，不是 `README.md` 内容引起的。
- `README.md` 内容无任何语法或规范问题，无需修改。

## 潜在风险
无。`README.md` 未做任何修改，不会引入任何风险。