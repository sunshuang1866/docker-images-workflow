# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 工具 `eulerpublisher` 的 appstore 发布规范检查器对 PR 中修改的 `README.md` 报告路径错误，声称期望路径应为 `/README.md`。但 `README.md` 位于仓库根目录，其路径本身就是 `/README.md`，CI 工具的判定与实际路径自相矛盾，属于 CI 工具自身的误报（假阳性）。

### 与 PR 变更的关联
本次 PR 为纯文档变更，仅修改了 `README.md` 和 `README.en.md` 中镜像 Tag 列表的描述（更新 `24.03-lts-sp2` → `24.03-lts-sp3` 作为 latest，新增 `25.09` / `24.03-lts-sp3` / `24.03-lts-sp2` 条目）。PR 未修改任何 Dockerfile、`image-list.yml`、`meta.yml` 或应用镜像文件。

CI appstore 规范检查器在扫描 PR 变更文件时，对根目录 `README.md` 触发了路径校验规则，给出自相矛盾的错误报告（文件路径即期望路径），导致构建被标记为失败。该失败与 PR 的实际代码/文档变更内容无关，属于 CI 基础设施层面的误判。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher` 中 appstore 发布规范检查器的路径校验逻辑存在 bug：对根级 `README.md` 文件做路径比对时，可能因路径格式不一致（如前置 `/` 的处理差异）导致误报 FAILURE。需排查 `update.py` 中路径校验函数的实现（特别是第 273 行附近的路径比对逻辑），确认是否存在 leading-slash 归一化缺陷。

### 方向 2（置信度: 低）
此 PR 为纯文档 PR（仅修改 README），不涉及任何应用镜像的 Dockerfile 或元数据变更。CI appstore 发布规范检查器可能不应针对此类 PR 执行路径校验。可在 CI 流水线的触发条件中增加判断：如果 PR 变更文件不包含任何应用镜像目录下的文件（如无 Dockerfile、image-list.yml、meta.yml 变更），则跳过 appstore 规范预检步骤。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 附近路径校验函数的具体实现，确认路径比对逻辑是否对根目录文件存在 leading-slash 归一化问题。
2. 同一 CI 工具对纯文档 PR 的历史处理行为——是否有其他仅修改 `README.md` 的 PR（如 PR #2308 `AI/diskann/README.md`）也触发了同样的路径校验误报。
3. 该 appstore 规范预检的触发条件——是否无论 PR 修改了什么文件都会执行路径校验，还是存在过滤逻辑。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——此失败为 CI 工具自身逻辑问题，不涉及对外部源文件的正则 patch。）
