# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验失败
- 新模式症状关键词: Path Error, expected path, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489 - INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,839 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI appstore 发布规范检查工具 `update.py` 检测到 `README.md` 变更后，将其纳入发布规范校验流程。工具从 git diff 中获取的文件路径为 `README.md`（无前导 `/` 的相对路径），与校验规则中期望的绝对路径 `/README.md` 进行字符串比对时产生不匹配，触发 `[Path Error]` 失败。仓库根目录的 `README.md` 实为项目文档而非应用镜像发布制品，不应被 appstore 校验流程拦截。

### 与 PR 变更的关联
PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md` 两个文档文件（新增基础镜像 tag 条目），无任何应用镜像 Dockerfile 或元数据文件变更。CI 失败由 CI 工具自身的路径规范化问题导致——`git diff` 输出的相对路径 `README.md` 被传入 appstore 校验逻辑，与期望的绝对路径 `/README.md` 产生字符串不匹配。PR 改动内容本身无问题。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `update.py` 应在进行 appstore 发布规范校验前，对 git diff 输出的变更文件路径进行归一化处理（补前导 `/`），使其与校验规则中期望的路径格式一致。同时建议 CI 工具增加过滤逻辑：根目录下的文档文件（`README.md`、`README.en.md`、`LICENSE` 等）不应进入 appstore 发布规范校验流程，因为这类文件不属于应用镜像发布制品。

### 方向 2（置信度: 低）
本次 PR 的实际目的为关闭 issue #3153（更新 README 中过时的基础镜像 tag 链接）。如果 PR 的合并门禁允许跳过 appstore 校验（如添加 skip ci 标记或由 reviewer overridden merge），可在不修改 CI 工具的情况下直接合并该纯文档 PR。

## 需要进一步确认的点
1. CI 工具 `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现——是字符串精确匹配还是路径规范化后的比较。
2. 该 CI appstore 预检是否有文档类文件的豁免列表或跳过机制。
3. 过去是否存在类似纯文档 PR（仅修改 README）通过该 CI 检查的案例，以排除是否为 CI 环境近期变更引入的回归问题。

## 修复验证要求
若选择修复方向 1，code-fixer 需在 CI 工具仓库中找到 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑，确认当前实现方式（字符串精确比对 vs 路径规范化比对），然后对 git diff 输出的路径进行归一化或增加文档文件过滤逻辑。提交前需在 CI 环境中重新触发该检查，验证纯 README 变更的 PR 可以通过校验。
