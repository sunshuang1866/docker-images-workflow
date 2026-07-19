# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI路径格式校验过严
- 新模式症状关键词: README.md, Path Error, expected path, appstore, /README.md

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范检查步骤）
- 失败原因: PR #2790 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（纯文档更新），但 CI 的 appstore 发布规范检查工具对所有变更文件执行路径格式校验。该检查将 git diff 输出的无前导斜杠路径 `README.md` 与期望的带前导斜杠路径 `/README.md` 进行严格字符串比较，两者不匹配导致判定为 FAILURE。此根级文档变更不应被纳入应用镜像提交规范检查范围。

### 与 PR 变更的关联
PR 变更本身无任何代码或配置质量问题。变更内容仅限于 `README.md` 和 `README.en.md` 中标签列表的更新（新增 `24.03-lts-sp3`、`25.09` 标签，重新排列条目）。CI 失败是由 CI 工具的路径校验逻辑过于严格、未排除仓库根级文档文件所致，属于 CI 基础设施问题，与 PR 改动内容无关。

## 修复方向

### 方向 1（置信度: 高）
CI 编排工具（`eulerpublisher` 的 appstore 检查模块）需对根级 README.md / README.en.md 文件进行豁免处理，不应将仓库根目录的文档文件纳入"应用镜像提交规范"的路径校验流程。可通过在 `update.py` 的路径收集阶段过滤掉仅有根级 README 变更（无 Dockerfile、meta.yml、image-info.yml 等镜像相关文件）的 PR。

### 方向 2（置信度: 中）
若 CI 工具短中期无法修改，可考虑在 CI 配置中对纯文档类 PR（仅变更 `README*.md` 文件且无其他文件变更）跳过 appstore 发布规范检查步骤。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现，确认路径对比方式及是否有文件排除列表。
- 该 CI 检查的历史行为：是否有其他纯文档 PR 也触发过同样错误，以确认是否为 CI 工具回归引入。
