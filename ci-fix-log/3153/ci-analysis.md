# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore specification check 阶段）
- 失败原因: CI appstore 发布规范检查工具 `eulerpublisher` 对 PR 中变更的 `README.md` 报出 `[Path Error]`，描述为 "The expected path should be /README.md"。但 PR 变更的 `README.md` 确实位于仓库根目录（即 `/README.md`），文件路径本身正确，错误信息与实际路径矛盾，疑似 CI 工具的路径校验逻辑存在 bug 或误判。

### 与 PR 变更的关联
PR #3153 仅修改了两个根目录文件：`README.md` 和 `README.en.md`，变更内容为纯文档更新——在基础镜像可用 tags 列表中新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目及其 openEuler 镜像站 URL，同时将 `24.03, latest` 标签从指向 SP1 更正为指向 SP4。

- 文件路径未发生变化（始终为根目录 `/README.md`），CI 声称的"期望路径 `/README.md`"与实际路径完全一致。
- 变更不涉及任何 Dockerfile、meta.yml、image-list.yml 等构建关键文件。
- **该失败与 PR 改动内容无直接因果关系**——PR 仅做文档更新，即使回退到旧版 README，只要文件被提交到该 CI 检查流程中，仍可能触发相同的路径校验错误。

## 修复方向

### 方向 1（置信度: 低）
该 CI 检查来自 `eulerpublisher` 工具的 appstore 发布规范校验。`README.md` 位于根目录 `/README.md` 却触发 "The expected path should be /README.md" 的 Path Error，很可能是 CI 工具内部的路径比较逻辑存在缺陷（如字符串比较未统一处理前导 `/`），或该检查本不应适用于根目录的 README 文件。
- 需 CI 平台/工具维护者检查 `eulerpublisher/update/container/app/update.py:273` 附近路径校验逻辑，确认是否存在对根目录 README.md 的误判。

### 方向 2（置信度: 低）
错误类型 `[Path Error]` 可能并非指文件的文件系统路径，而是指 README.md **内容中的 URL 路径引用**（如 `https://repo.openeuler.org/openEuler-25.09/docker_img/`）不符合某些校验规则。若 CI 工具会解析 README 中的镜像站 URL 并验证其可达性或格式，需确认新增 tags 对应的镜像站路径（如 `openEuler-25.09/docker_img/`）是否实际存在且可公开访问。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 附近的代码逻辑——该检查究竟校验的是文件自身的文件系统路径，还是文件内容中引用的 URL 路径？
2. CI 工具为何只将 `README.md` 列入 `Difference` 列表（日志 `INFO: Difference: ["README.md"]`），而忽略了同样被 PR 修改的 `README.en.md`？
3. 该 CI appstore 规范检查是否对所有涉及根目录 `README.md` 变更的 PR 均会产生同样的假阳性——即该检查规则是否本应仅适用于非根目录的 README 文件？
4. 同类纯文档 PR（仅修改 README）的历史 CI 状态——是否有成功通过的历史案例可参考？
