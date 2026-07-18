# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式（部分关联 模式11）
- 新模式标题: 根目录文件路径格式校验
- 新模式症状关键词: Path Error, expected path should be, README.md, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-.../update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 编排工具 `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检阶段）
- 失败原因: CI 的 appstore 发布规范校验器对 PR 中修改的 `README.md` 进行路径格式检查，校验器期望的路径格式为 `/README.md`（以 `/` 开头），但从 git diff 中提取的路径为 `README.md`（无前导 `/`），字符串比对不匹配，导致路径校验失败并终止流水线。

### 与 PR 变更的关联
PR 仅修改了两个 README 文件（`README.md` 和 `README.en.md`）的内容——更新基础镜像可用 Tags 列表（将 latest 从 24.03-lts-sp2 升为 24.03-lts-sp3、新增 25.09 和 24.03-lts-sp3 条目、修正 24.03-lts-sp2 的链接 URL）。这些**内容变更是合法且正确的**，不是导致 CI 失败的原因。

CI 失败与这个 PR 的关联在于：**只要 PR 修改了仓库根目录的 README.md，就会触发 CI appstore 路径校验器，而该校验器存在路径格式不匹配的问题**。即使 PR 内容是空操作（如只改一个空格），同样会触发此失败。这是一个 CI 工具对根目录级文件路径格式处理不当的问题，而非 PR 代码质量问题。

注意：CI 日志中仅检测到 `README.md` 有差异，未提及 `README.en.md`——这说明 `eulerpublisher/update.py` 的差异计算可能仅关注 `README.md` 或仅对特定文件名执行路径校验。

## 修复方向

### 方向 1（置信度: 中）
CI 校验工具 `update.py` 中路径提取逻辑在处理 git diff 变更文件列表时，未对根目录文件路径添加前导 `/` 进行标准化。修复方式是：在路径校验之前，对从 diff 中提取的路径进行归一化处理——若路径不以 `/` 开头则自动补全前导 `/`，使 `README.md` → `/README.md`。

### 方向 2（置信度: 低）
`update.py` 的路径校验预期值配置可能与其路径提取逻辑不一致：一个是 `/README.md`（硬编码或由配置决定），另一个是 `README.md`（由 git diff 解析产生）。修复方式是确认两侧使用相同的路径格式约定，或将校验改为使用相对路径格式。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 源码中第 273 行附近的 `ERROR` 日志输出逻辑，以及路径校验的前置提取与比对逻辑（第 356 行附近的差异计算），以确认路径标准化缺失的具体代码位置。
2. CI 的 appstore 发布规范配置中，根目录 `README.md` 是否应当被纳入校验范围——如果 README.md 不属于 appstore 发布规范的管辖范畴，则应将其加入白名单/排除列表，而非进行路径格式校验。
3. 同类 PR（仅修改根目录 README.md 的 PR）是否也曾触发此错误，以判断这是普遍问题还是本次 PR 的特定触发条件。

## 修复验证要求
无需额外验证步骤。该修复不涉及第三方/上游源文件的正则匹配。
