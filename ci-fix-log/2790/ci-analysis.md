# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用 — 匹配已有模式)
- 新模式症状关键词: (不适用 — 匹配已有模式)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 编排工具 appstore 发布规范预检）
- 失败原因: CI 的 `eulerpublisher` 工具检测到 PR 变更了仓库根目录的 `README.md`，随即对其执行 appstore 发布规范路径校验。`README.md` 是仓库根级文档文件（非 Docker 镜像目录下的文件），但 CI 工具仍将其纳入 appstore 规范检查范围并判定失败。该错误是 CI 工具的检查逻辑问题——对根级纯文档文件不恰当地套用了镜像路径校验规则。

### 与 PR 变更的关联
PR 的改动**不直接触发**该失败。PR #2790 仅修改了两个文档文件（`README.md` 和 `README.en.md`），更新了 openEuler 基础镜像 Tag 表格内容（新增 24.03-lts-sp3、25.09 等行，修正 latest 指向链接）。这些是纯文档维护性变更，未涉及任何 Dockerfile、meta.yml、image-list.yml 或编译构建脚本。CI 失败是 `eulerpublisher` 工具对根级文档文件执行了本不应执行的路径校验所致，属于 CI 基础设施层面的误报。

## 修复方向

### 方向 1（置信度: 低）
PR 本身无需修改。应确认 CI 编排层是否能识别并跳过仅含根级文档变更（不涉及 Docker 镜像）的 PR，避免触 appstore 规范检查。若 CI 工具不支持此类跳过逻辑，此问题可标记为已知的 CI 限制，不影响代码合并。

### 方向 2（置信度: 低）
若 CI 工具要求所有 PR 中变更的文件都需通过 appstore 规范检查（包括根级 `README.md`），则需确认 CI 工具版本是否存在 path 处理 bug——当前 `README.md` 本身已位于仓库根目录（即 `/README.md`），错误提示"expected path should be /README.md"与实际情况矛盾，可能指示 CI 工具在路径归一化或比较逻辑上存在缺陷。

## 需要进一步确认的点
- CI `eulerpublisher` 工具是否有白名单机制跳过根级纯文档文件的校验？若无，是否为工具的设计预期行为？
- `update.py:273` 中 `README.md` 被判定路径不符的具体判定逻辑是什么？当前文件路径 `/README.md` 与"期望路径 `/README.md`"一致却仍报 FAILURE，是否存在字符串比较 bug（如首斜杠缺失/冗余、大小写敏感等）？
- 同类纯文档 PR 在此仓库的历史 CI 执行记录——是否有仅修改 `README.md` 的 PR 此前也失败，还是此为首次出现？

## 修复验证要求
（不适用 — 本次失败为 infra-error 类型，不涉及 Dockerfile / 补丁 / 正则 patch 修改，无需 code-fixer 处理。）
