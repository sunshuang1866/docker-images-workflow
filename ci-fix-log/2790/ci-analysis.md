# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检阶段）
- 失败原因: CI 的 appstore 发布规范校验工具检测到 PR 变更了仓库根目录的 `README.md`，但该校验工具的设计预期是处理 `{category}/{image}/{version}/{os-version}/` 路径结构的 Docker 镜像目录文件。当遇到根目录级别的文档文件（`README.md`、`README.en.md`）时，校验逻辑无法将其归入任何镜像目录路径模式，从而抛出 `[Path Error]`。

值得注意的是，`README.md` 本身就位于仓库根目录 `openeuler-docker-images/README.md`，即其路径就是 `/README.md`，与校验工具报告"期望路径应为 `/README.md`"一致。然而校验仍判定 FAILURE，说明该校验器实际上要求文件必须位于镜像目录层级（如 `SomeCategory/SomeImage/1.0/24.03-lts-sp4/`）下，而非仓库根目录。

### 与 PR 变更的关联
PR #2790 仅修改了两个文件——`README.md` 和 `README.en.md`，均为仓库根目录下的文档文件。变更内容是更新"可用镜像的 Tags"列表（新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，将 latest 指向从 `24.03-lts-sp2` 改为 `24.03-lts-sp3`）。PR 本身不涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 的修改。

因此，PR 改动是纯文档更新，没有代码或构建逻辑错误。CI 失败是由 CI 校验工具对根目录文件类型的处理不当所引起。

## 修复方向

### 方向 1（置信度: 低）
CI 工具 `eulerpublisher/update/container/app/update.py` 在处理变更文件列表时，未区分"根目录文档文件"与"镜像目录构建文件"两种场景。当 PR 仅包含根目录文档变更（不含镜像目录变更）时，校验器可能应将此类 PR 视为免检放行，而非报告路径错误。需要排查 `update.py` 中对非镜像目录文件的处理分支，确认是否缺少对根目录级 `README.md`/`README.en.md` 等文件的免检逻辑。

但此修复需要对 CI 工具的流水线代码（`eulerpublisher` 仓库）进行改动，超出当前 openeuler-docker-images 仓库的范围。Code Fixer 应优先确认：此类文档纯更新 PR 在现有 CI 规范下是否被期待通过 appstore 校验。

### 方向 2（置信度: 低）
另一种可能性：`update.py` 在第 222 行成功 clone 了 PR 源分支仓库后，其变更差异检测逻辑可能有缺陷，导致实际检测到的文件路径格式与预期格式不匹配（例如带/不带前导 `/`、相对路径 vs 绝对路径）。若该缺陷是字符串匹配层面的 bug，则修复应在 `eulerpublisher` 仓库的 `update.py` 中进行。

## 需要进一步确认的点
1. 当前 openEuler 容器镜像仓库的 CI 流水线中，纯文档更新 PR（如仅修改根目录 README）是否被允许且预期能通过 appstore 释放规范校验？如果是，则 `eulerpublisher` 的 `update.py` 存在 bug 需要修复。
2. 日志中 `Difference: ["README.md"]` 仅列出了 `README.md`，而 PR diff 同时修改了 `README.en.md`。需确认差异检测是否遗漏了 `README.en.md`，以及两个文件是否都应被检查。
3. 若需修复 `update.py`，需获取 `eulerpublisher` 仓库的源代码，确认该校验逻辑的具体实现方式。

## 修复验证要求
（不适用 — 失败类型为 infra-error，不涉及 Dockerfile、补丁或正则在外部源文件中的修改。）若后续确认需要修改 `eulerpublisher` 中的校验逻辑，code-fixer 必须首先获取 `eulerpublisher` 仓库中对 `update.py` 文件的最新代码，理解 `line:273` 附近的校验分支逻辑，再决定修复方案。
