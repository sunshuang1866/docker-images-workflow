# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 脚本 `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检步骤）
- 失败原因: CI 的 appstore 发布规范校验步骤对所有 PR 中变更的文件进行路径校验，`README.md` 和 `README.en.md` 是仓库根目录的文档文件，不属于应用镜像路径（AI/、Bigdata/、Cloud/ 等），因此被校验工具标记为 `[Path Error]`，期望路径指向 `/README.md`。

### 与 PR 变更的关联
**强关联**。PR 仅修改了 `README.md` 和 `README.en.md` 两个根目录文档文件（更新可用基础镜像 tag 列表），未涉及任何应用镜像的 Dockerfile、meta.yml、image-info.yml 等文件。CI 的 appstore 校验逻辑未区分"文档类 PR"和"应用镜像类 PR"，对文档变更也执行了路径校验，导致两个 README 文件被判定为不符合规范。这类 PR 变更本不应触发 appstore 发布规范检查，或应在检查中被豁免。

## 修复方向

### 方向 1（置信度: 高）
CI 的 appstore 发布规范校验脚本（`eulerpublisher/update/container/app/update.py`）应在检测到变更文件全部为仓库根目录的非应用镜像文件（如 README.md、README.en.md、.gitignore 等）时，跳过路径校验并直接通过。具体策略：
- 在 `update.py` 中增加文件变更类型的判断逻辑：若所有变更文件均不在应用镜像目录（AI/、Bigdata/、Storage/、Database/、Cloud/、HPC/、Distroless/、Others/、Base/）下，则视为纯文档/配置变更，不触发 appstore 发布规范校验，直接返回成功。
- 或者，在校验清单中显式豁免已知根目录文件（README.md、README.en.md、LICENSE 等）。

### 方向 2（置信度: 低）
该 PR 是纯文档更新，本可通过 CI 的文档变更快速通道或由仓库管理员手动合并。若 `update.py` 不可修改，可考虑在 CI Pipeline 层面增加条件判断：当 PR 仅包含根目录文档文件变更时，跳过 appstore 校验 stage。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中 `_check_path` 或类似函数的具体实现逻辑，确认其是否已有文档豁免机制但存在 bug（如路径比较时对 `/` 前缀的处理不一致）。
- CI Pipeline（Jenkins）的流水线配置中，appstore 校验 stage 是否有条件过滤机制，以及是否可在此处增加文档类 PR 的豁免条件。
- 确认该 PR 在 PR #3153 之前是否有类似纯文档 PR 成功通过 CI 的历史案例，以判断这是最近引入的 CI 行为变更还是长期存在的问题。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用 — 本次故障涉及的 CI 脚本为仓库内部工具，不涉及外部源文件的正则匹配。）
