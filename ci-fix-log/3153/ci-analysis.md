# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式 模式可归入模式11的扩展变体）
- 新模式标题: 根目录文件路径校验误报
- 新模式症状关键词: Path Error, expected path, appstore, README.md, update.py

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检步骤）
- 失败原因: CI appstore 路径校验工具将 PR 修改的根目录文件 `README.md`（git diff 输出无前导 `/`）与预期格式 `/README.md`（带前导 `/`）进行字符串比对，判定为路径不匹配，报 `[Path Error]`。该 PR 仅修改 README 文档，不涉及任何应用镜像的 Dockerfile、meta.yml 或 image-info.yml，appstore 路径校验本身不应被触发或应对纯文档变更 PR 放行。此为 CI 工具误报，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 中以"Supported Tags / 可用镜像的Tags"段落，更新了基础镜像可用 tag 列表（新增 `24.03-lts-sp4`/`24.03-lts-sp3`/`25.09` 条目，修正 `24.03-lts-sp2` 的 URL）。这些改动是纯文档更新，未涉及任何 `image-list.yml`、`meta.yml`、`image-info.yml` 或 Dockerfile，不应被 appstore 发布规范校验拦截。CI 失败与此次 PR 变更无实质关联，属 CI 工具层面的假阳性。

## 修复方向

### 方向 1（置信度: 高）
CI 维护方修复 `eulerpublisher/update/container/app/update.py` 中的路径比对逻辑：
- 对 git diff 输出的文件路径做前导 `/` 标准化（`README.md` → `/README.md`）；
- 或对根目录的非 image 文件（如 `README.md`、`README.en.md`、`LICENSE` 等）直接跳过 appstore 路径校验。

### 方向 2（置信度: 中）
CI 维护方检查触发条件：当前 appstore 路径校验是否对纯文档变更的 PR 也触发了，若触发应增配跳过规则（如仅 tracking 场景目录 `Bigdata/`、`AI/`、`Database/` 等下的文件变更才执行 appstore 校验）。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py:222-273` 中的路径比对逻辑具体实现：路径标准化是否缺失前导 `/` 补全步骤。
- 确认 CI 触发条件：appstore 校验是否应按 PR 变更文件类型筛选（仅非 image 目录文件的 PR 应跳过）。
- 若 CI 配置中有文件过滤白名单/黑名单机制，确认 `README.md` 是否需要纳入豁免列表。

## 修复验证要求
无需 code-fixer 参与，此为 CI 基础设施（`eulerpublisher` 工具）问题，应由 CI 维护方处理。
