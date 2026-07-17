# 修复摘要

## 修复的问题
无需代码修改。该 CI 失败属于基础设施问题（infra-error），非源代码缺陷。

## 修改的文件
无（无需修改任何源代码文件）

## 修复逻辑
PR #2790 是纯文档修正（更新根目录 README.md 中基础镜像的 Tags 列表），未涉及任何 appstore 应用镜像相关文件。CI pipeline 的 `eulerpublisher` appstore 发布规范预检工具要求所有被检文件必须符合 `{category}/{image-name}/{version}/{os-version}/` 的 appstore 镜像目录路径规范，根目录 README.md 是项目级文档文件，不属于任何 appstore 应用镜像发布条目，因此路径校验失败。

这不是源代码 bug，而是 CI pipeline 的触发/检查范围问题——该预检不应将项目根目录的 README.md 纳入 appstore 镜像路径校验。需由 CI 流水线维护方调整以下之一：
- 将 `README.md` / `README.en.md` 加入 appstore 预检白名单/排除列表
- 或使该 CI pipeline 仅对匹配 appstore 镜像路径模式的 PR 触发

## 潜在风险
无。未对源代码做任何修改，不存在引入新问题的风险。