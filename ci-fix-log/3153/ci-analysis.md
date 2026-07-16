# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: —
- 新模式症状关键词: —

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-...-INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具 (`update.py`) 对 PR 变更文件进行路径校验时，git diff 产出的路径 `README.md`（无前置 `/`）与 CI 工具期望的规范路径 `/README.md`（带前置 `/`）不匹配，触发 `[Path Error]`。

### 与 PR 变更的关联
**直接关联。** 本 PR 仅修改了 `README.md` 和 `README.en.md` 两个根目录文档文件（更新基础镜像可用 Tags 列表），任何应用镜像元数据（Dockerfile、meta.yml、image-info.yml 等）均未变更。CI 扫描 PR diff 时检测到 `README.md` 变更，对其执行 appstore 发布规范路径校验，因路径格式不匹配而失败。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `update.py` 中的路径比较逻辑可能存在严格匹配缺陷——git diff 产出的路径通常无前置 `/`（如 `README.md`），而 CI 工具内部期望带前缀的绝对路径（如 `/README.md`）。需检查 `update.py` 的路径规范化/比较逻辑，确保在比较前对 diff 路径和期望路径做统一的规范化处理（如均添加或均移除前置 `/`）。

### 方向 2（置信度: 低）
若路径比较逻辑本身无误，则该检查可能原本不应对纯文档 PR（仅修改 README 文件、无 Dockerfile/meta.yml 等应用镜像元数据变更）触发。需检查 CI 流水线中 appstore 预检的触发条件：纯文档变更的 PR 是否应跳过 appstore 发布规范检查。

## 需要进一步确认的点

1. **`update.py` 路径校验的源码**：需查阅 `eulerpublisher/update/container/app/update.py` 第 222–273 行的具体实现，确认路径比较的规范化方式（是否存在 `README.md` 与 `/README.md` 的格式不一致）。
2. **CI 预检的跳过条件**：需确认 appstore 发布规范预检是否有跳过纯文档 PR 的机制——若 PR 仅修改根目录 README 且不包含任何 `Dockerfile`/`meta.yml`/`image-info.yml` 变更，是否应跳过该检查。
3. **README.en.md 为何未被标记**：日志中 diff 仅显示了 `README.md` 的变更，但 PR diff 确认 `README.en.md` 也发生了相同内容的修改。需确认 `README.en.md` 是否在 CI 检查中被排除、或是日志截断导致未显示。
