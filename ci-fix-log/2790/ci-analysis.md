# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检流程）
- 失败原因: CI 内置的 `eulerpublisher` appstore 校验工具将根目录 `README.md`（纯文档文件，属于仓库自述文档而非应用镜像发布物）错误地纳入 appstore 发布规范路径校验，检测到的路径 `README.md`（diff 输出不带前导 `/`）与校验器期望的路径 `/README.md`（带前导 `/`）不匹配，导致校验失败。该文件本身不应参与 appstore 路径检查。

### 与 PR 变更的关联
PR #2790 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（更新支持的镜像 Tags 列表，如新增 `24.03-lts-sp3`、`25.09` 等条目），属于纯文档维护变更，未涉及任何 Dockerfile、meta.yml、image-info.yml 等应用镜像相关文件。

CI diff 检测工具（`update.py:356`）捕获到 `README.md` 被修改后，将其送入 appstore 发布规范检查流程。由于根级自述文档不在 appstore 应用镜像发布范围内，CI 工具对其执行路径校验本身即为错误行为。PR 内容无问题，失败由 CI 工具校验逻辑缺陷导致。

## 修复方向

### 方向 1（置信度: 高）
CI `eulerpublisher` 工具的 appstore 路径校验逻辑应排除仓库根目录级文档文件（如 `README.md`、`README.en.md`、`LICENSE` 等），仅对应用镜像目录（`AI/`、`Bigdata/`、`Database/` 等）下的文件执行路径校验。或修正 diff 输出路径与校验期望路径之间前导 `/` 不一致的问题，使根级文件的校验不会因路径格式差异而误报。

此修复需在 `eulerpublisher/update/container/app/update.py` 中实现文件路径过滤或路径格式标准化，无需修改 PR 内容。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py` 中第 273 行附近 appstore 路径校验函数的完整实现，排查为何根级纯文档文件会被纳入 appstore 发布检验范围。
- 确认 `README.en.md` 也被修改但未出现在 `Difference` 列表中（日志仅输出 `["README.md"]`）的原因，确保 PR 的完整变更集均被正确处理。

## 修复验证要求
不适用。本失败为 CI 基础设施工具（eulerpublisher）的校验逻辑缺陷，与 PR 的 Dockerfile 或应用镜像文件变更无关，无需对 PR 仓库文件做任何修改。
