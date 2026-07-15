# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（变体：根级 README 路径校验误报）

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-...-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,832-...-INFO: Clone https://gitcode.com/sunshuang1866/****-docker-images.git successfully.
2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI appstore 发布规范预检阶段（`eulerpublisher/update/container/app/update.py:273`）
- 失败原因: CI 的 appstore 路径校验对根级 `README.md` 报告 `[Path Error]`，声称期望路径为 `/README.md`。但根据 PR diff（`--- a/README.md` / `+++ b/README.md`），文件确实位于仓库根目录（即 `/README.md`），实际路径与期望路径一致，该校验结果与文件实际位置矛盾，属于 CI 工具路径比对逻辑的误报或归一化 bug（如 `README.md` vs `/README.md` 的斜杠前缀差异）。

### 与 PR 变更的关联
**与 PR 无关**。PR #3153 仅修改了根级 `README.md` 和 `README.en.md` 中基础镜像 Tags 列表的内容（更新 `latest` 标签从 `24.03-lts-sp2` → `24.03-lts-sp4`，新增 `24.03-lts-sp3`、`25.09` 等条目，并修正对应 URL），不涉及任何文件增删、重命名或目录结构调整。CI 报出的路径错误源于 appstore 规范校验工具对根级文档文件的不当检查，非 PR 变更触发。

## 修复方向

### 方向 1（置信度: 中）
CI 的 `eulerpublisher` appstore 路径校验工具路径比较时存在字符串匹配缺陷——检测到的路径为 `README.md`（不带前导 `/`），而期望路径为 `/README.md`（带前导 `/`），两者因前导斜杠差异误判为不匹配。这属于 CI 工具本身的 bug，需由 CI 维护方修复路径归一化逻辑，**PR 无需修改**。

### 方向 2（置信度: 低）
Appstore 发布规范可能不允许在镜像提交类 PR 中修改根级 `README.md`（该文件属于仓库级文档，不属于任何镜像目录）。若规范确实有此限制，则 PR 的 README 修改需要以其他形式（如单独的非 appstore PR）提交。但即便如此，错误消息 `[Path Error] The expected path should be /README.md` 依然与实际情况矛盾（文件确实在此路径），说明 CI 校验工具的错误提示不准确，仍需 CI 侧修正。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径比较逻辑的具体实现，确认是否因前导 `/` 归一化缺失导致误报。
2. Appstore 发布规范是否允许在镜像发布 PR 中修改根级 `README.md` 和 `README.en.md`——若不允许，CI 应产出语义更明确的错误信息（而非误导性的路径错误），且需明确此类文档变更的合规提交流程。
3. `README.en.md` 同样被 PR 修改但未出现在 CI diff 列表中（仅检测到 `README.md`），需确认这是 CI 有意排除还是检测遗漏。
