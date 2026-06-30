# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式（关联模式11）
- 新模式标题: README路径校验失败
- 新模式症状关键词: Path Error, The expected path should be, README, appstore, update.py

## 根因分析

### 直接错误
```
2026-06-30 11:28:09,089 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 中 `eulerpublisher` 工具的 appstore 发布规范预检逻辑触发——该检查扫描 PR 中变更的所有文件，对 `README.en.md` 的校验失败（主因）：工具只认 `/README.md` 这一条合法路径，`README.en.md` 不在 appstore 发布规范认可的文件清单内。`README.md` 的同步报错可能是工具的级联误报或该文件内容缺少 appstore 发布所需的元数据格式（如 Copyright + SPDX 声明头）。

### 与 PR 变更的关联
**直接关联**。PR #2790 仅修改了 `README.md` 和 `README.en.md` 两个根目录下的文档文件（添加新的镜像 Tag 条目和调整链接），无任何 Dockerfile、image-info.yml、meta.yml 等应用镜像构建文件。CI 的 appstore 发布规范预检 (`update.py`) 会对所有变更文件进行合规性校验，纯文档类 PR 中 `README.en.md` 不在认可文件清单内，因而直接触发 Path Error。

## 修复方向

### 方向 1（置信度: 中）
`README.en.md` 不在 appstore 发布规范认可的文件清单中。如果该文件确实需要保留在仓库中，需在 CI 的 appstore 校验逻辑 (`eulerpublisher/update/container/app/update.py`) 中将 `README.en.md` 加入白名单/豁免列表，使其不被视为"需符合发布规范"的变更文件。或者，如果该 PR 不应该触发 appstore 发布检查（因为不涉及任何镜像发布），可在 trigger 层面排除纯文档 PR。

### 方向 2（置信度: 低）
`README.md` 本身也报 Path Error，但根路径 `/README.md` 正是其实际路径。可能原因：`update.py` 在检查变更文件时，对根目录下的 README 文件有额外的内容校验（如要求包含特定的 Copyright + SPDX 声明头或特定的 appstore 元数据格式），而当前内容不满足此要求。需查看 `update.py:273` 附近的校验逻辑确认。

## 需要进一步确认的点
1. 查看 `eulerpublisher/update/container/app/update.py` 第 273 行附近的校验逻辑，确认 Path Error 的具体触发条件——是基于文件路径白名单还是基于文件内容格式
2. 确认 `README.en.md` 是否在 appstore 发布规范中有任何定义（若没有，可能需要在 CI 配置中将其加入豁免列表）
3. 确认当前 `README.md` 是否缺少 CI appstore 检查要求的 Copyright + SPDX 声明头（模式17），若缺少则同时是另一个独立问题
4. 该 CI 构建由 PR #2809（`sunshuang1866:fix/2790 -> master`）触发，需确认 PR #2790 与 #2809 的关系，确认构建的 diff 与实际要检查的内容是否一致

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本问题不涉及修改正则匹配第三方/上游源文件。
