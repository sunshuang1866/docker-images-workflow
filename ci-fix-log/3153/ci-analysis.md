# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 根目录README路径校验误报
- 新模式症状关键词: Path Error, The expected path should be, /README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,839-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范检查）
- 失败原因: CI 工具 `eulerpublisher` 的 appstore 路径校验逻辑在比较 git diff 输出的路径 `README.md`（无前导 `/`）与预期路径 `/README.md`（含前导 `/`）时，因路径格式不一致（缺少前导 `/` 归一化）导致误判为路径错误。`README.md` 实际位于仓库根目录，路径完全正确。

### 与 PR 变更的关联
**与 PR 变更无直接关联**。本 PR 仅修改了两个文档文件（`README.md`、`README.en.md`），更新了基础镜像的可用 tags 列表，未涉及任何 Dockerfile、构建脚本或应用镜像元数据。CI 失败是由 `eulerpublisher` 工具的路径校验逻辑缺陷（未能归一化 git diff 输出的相对路径与内部预期的绝对路径格式）触发的误报，属于基础设施/工具问题。

## 修复方向

### 方向 1（置信度: 低）
CI 工具 `eulerpublisher` 的 `update.py` 中 appstore 路径校验逻辑存在缺陷：`git diff` 产出的变更文件路径不含前导 `/`（如 `README.md`），而下游校验器按含前导 `/` 的格式（如 `/README.md`）做精确字符串比对，导致完全正确的仓库根目录文件被误判为"路径错误"。需修复 `eulerpublisher` 工具代码中的路径归一化逻辑，使其在校验前将两种格式统一。此为工具侧修复，无需修改本 PR 的任何文件。

### 方向 2（置信度: 低）
若 `eulerpublisher` 工具的设计意图是只校验镜像子目录（如 `AI/xxx/...`）下的文件，而非仓库根目录的 README，则可能是工具在过滤变更文件时未能将根目录 `README.md` 排除在校验范围之外。需在工具的文件筛选逻辑中添加白名单或路径前缀过滤，使非镜像目录下的文件变更免于 appstore 路径校验。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:260-280` 的路径校验函数的具体实现逻辑——它如何获取"实际路径"并与"预期路径"做比对，是否存在路径归一化步骤。
2. 同一 CI job 日志中仅出现 `README.md` 的报错，但 PR 实际还修改了 `README.en.md`——为什么 `README.en.md` 没有被检测到？这可能暗示工具的 diff 解析逻辑也有问题。
3. 日志中 `Difference: ["README.md"]` 仅含一个文件而 PR 改了俩，需确认 `eulerpublisher` 的变更检测模块（`update.py:356`）是否因某种原因只识别了部分变更。
4. 此前的 PR 是否也出现过仅修改根目录 README 而触发此路径错误的情况——若存在，则可确认这是 CI 工具侧的已知缺陷而非本 PR 引入的新问题。

## 修复验证要求
无需 code-fixer 行动。此为 `eulerpublisher` CI 工具自身的路径校验缺陷，应与本 PR 的文档变更解耦处理。建议将此问题提报给 CI 基础设施团队修复工具逻辑。
