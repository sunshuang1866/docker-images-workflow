# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级文件触发appstore路径校验
- 新模式症状关键词: README.md, Path Error, expected path should be, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489 - update.py[line:356] - INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,832 - update.py[line:222] - INFO: Clone https://gitcode.com/sunshuang1866/****-docker-images.git successfully.
2026-07-14 11:28:17,839 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具 `update.py` 对 PR 中变更的根级 `README.md` 执行了路径校验，报告 "The expected path should be /README.md" 并判定 FAILURE。而该文件实际路径正是 `/README.md`，说明 CI 工具存在路径字符串比较方式不一致的问题（diff 输出的路径为 `README.md` 无前导 `/`，而校验期望路径为 `/README.md` 带前导 `/`），或 CI appstore 校验器本身不支持验证根级文件的路径格式。

### 与 PR 变更的关联
PR 仅修改了两个根级文档文件（`README.md` 和 `README.en.md`），更新了基础镜像可用 tag 列表（新增 24.03-lts-sp4/sp3/sp2 和 25.09 条目）。失败与 PR 的文档内容变更**无直接关系**——CI 失败的原因是 appstore 路径校验工具对根级文件进行了错误的校验，而非文档内容本身有问题。

## 修复方向

### 方向 1（置信度: 中）
根级 `README.md` 文件的修改不应触发 CI appstore 路径校验。CI 校验逻辑（`eulerpublisher/update/container/app/update.py`）应将根级文件（`README.md`、`README.en.md`、`LICENSE` 等）排除在 appstore 发布规范检查范围之外。这属于 CI 基础设施工具的行为修正，需要修改 `eulerpublisher` 仓库中的 `update.py` 脚本逻辑。

### 方向 2（置信度: 低）
如果 CI 工具不支持跳过根级文件检查，且 PR 需要合入，可尝试将本次修改拆分为仅包含 `README.md` 更改的独立提交，看是否能绕过 appstore 校验（但此方向不解决根本问题）。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中行 273 附近的完整校验逻辑，确认是否为路径字符串比较方式不一致导致（diff 输出无前导 `/` 的 `README.md` 与期望带前导 `/` 的 `/README.md` 不匹配）。
- 同类 PR（仅修改根级 `README.md` 的文档类 PR）在历史中是否也遭遇相同失败，以确认是否为已知的 CI 工具限制。
- 如果 `update.py` 不在本仓库内（属于 `eulerpublisher` 外部工具包），则此处修复需要由 CI 平台团队完成，本 PR 无法直接处理。
