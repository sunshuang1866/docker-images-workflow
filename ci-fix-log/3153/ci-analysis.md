# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,839-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具（eulerpublisher）对仓库根目录的 `README.md` 执行路径校验时，将该文件判定为不符合 appstore 上架路径规范。PR 仅修改了仓库级别的文档（`README.md` 和 `README.en.md`），并非提交新的应用镜像，但 CI 工具仍将其纳入了 appstore 路径校验流程，产生了误报。

### 与 PR 变更的关联
- **PR 变更与失败无关**。PR #3153 仅更新 README 文档中可用基础镜像 Tags 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09` 等条目，修正 latest 指向），不涉及任何 Dockerfile、meta.yml、image-list.yml 或应用镜像相关文件。
- CI 失败的原因是 `eulerpublisher` 工具对 `README.md` 的路径校验逻辑：该工具对比 git diff 产物中的文件路径 `README.md` 与期望路径 `/README.md`，产生 `[Path Error]`。`README.md` 位于仓库根目录，路径本身合法，该检查为 CI 工具层面的误报。

## 修复方向

### 方向 1（置信度: 中）
**CI 工具应跳过根目录 README 文件的 appstore 路径校验**。`eulerpublisher` 的 `update.py`（约第 222-273 行的 appstore 规范检查逻辑）在处理通过 git diff 检测到的变更文件时，不应将仓库根目录级别的文档文件（`README.md`、`README.en.md`）纳入 appstore 路径校验。可在 CI 工具侧添加白名单过滤（排除仓库根级文档文件），或由 PR 侧在提交时确保变更不触发该检查路径。

### 方向 2（置信度: 低）
**路径格式不一致导致比较失败**。`update.py` 中路径比较可能期望文件路径以 `/` 为前缀（即 `/README.md`），而 git diff 输出无前缀的 `README.md`，导致严格字符串比较失败。如果该问题是 CI 工具的已知行为，修复应在 `eulerpublisher` 仓库中进行。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 222-273 行的具体路径校验逻辑——确认为何 git diff 输出 `README.md` 被判定为不符合 `/README.md` 路径规范。
2. CI 工具设计意图——appstore 规范检查是否应当排除仓库根目录下的非应用镜像文件。
3. 是否存在 CI 工具版本更新或配置变更可解决此问题（参考 模式11 中同类的路径校验失败案例）。

## 修复验证要求
由于本报告判定为 `infra-error`（CI 工具层面的问题），若修复方向涉及修改 Dockerfile 或 README 内容，无需额外验证上游源文件。若修复方向涉及修改 `eulerpublisher` 工具代码，则需在 `eulerpublisher` 仓库内验证修改后的路径校验逻辑不会影响正常的应用镜像提交流程。
