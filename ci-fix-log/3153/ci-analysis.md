# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级README路径格式校验
- 新模式症状关键词: Path Error, expected path should be, README.md, appstore, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-.../update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 工具 `eulerpublisher` 对变更文件 `README.md` 执行路径校验时，将不带前导 `/` 的相对路径表示 `README.md` 与带前导 `/` 的期望绝对路径 `/README.md` 进行字符串比对，判定为路径格式不匹配。`README.md` 实际位于仓库根目录（即 `/README.md`），不存在路径错误，该失败为 CI 工具自身的路径表示一致性缺陷。

### 与 PR 变更的关联
PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md` 两个文档文件，更新了可用基础镜像 tag 列表（将 `latest` 从 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`，并补充了 `24.03-lts-sp3`、`25.09` 等新增 tag）。变更不涉及任何 Dockerfile、meta.yml、image-list.yml 或应用镜像构建文件。CI appstore 预检工具因检测到 `README.md` 有变更而触发了路径校验逻辑，随后因工具内部路径表示格式不一致而误报失败。

## 修复方向

### 方向 1（置信度: 中）
CI 失败为 `eulerpublisher` 工具内部的路径表示不一致导致——git diff 返回的路径为相对格式（无前导 `/`），而工具的路径校验模板使用绝对格式（有前导 `/`），字符串比较不相等。这不是 PR 代码本身的问题，PR 的 README 文档变更合法且位于正确路径。Code Fixer 无需修改 PR 中的任何文件。此问题应提交给 CI 基础设施团队修复 `eulerpublisher/update/container/app/update.py` 中的路径比较逻辑，使其对路径格式做归一化处理后再比对。

## 需要进一步确认的点
- 确认 `update.py:273` 附近的路径校验逻辑是否确实使用了字符串直接比较，而非路径归一化后的比较。
- 确认 `update.py:356` 中 `Difference` 列表获取的路径格式是否来自 `git diff --name-only`（输出为相对路径）。
- 确认同一 CI 流水线中其他 job（如 aarch64 架构构建 job）是否也有失败，若仅此 job 失败，则进一步佐证为工具自身问题。

## 修复验证要求
（不适用 — PR 本身无需修改，问题在 CI 工具侧）
