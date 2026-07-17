# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: README 路径校验失败
- 新模式症状关键词: Path Error, expected path, /README.md, appstore check

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-INFO: Difference: [
    "README.md"
]
...
2026-07-16 20:34:43,051-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 工具 `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具在路径校验阶段失败。工具检测到 `README.md` 被修改，但对路径进行校验时，内部格式比对不匹配——被检路径为相对路径 `README.md`（无前导 `/`），而校验规则中的期望路径为绝对路径 `/README.md`（含前导 `/`），导致路径检查报 FAILURE。PR 仅修改了根层级 `README.md` 和 `README.en.md` 的内容（新增镜像 Tag 条目），文件路径本身正确。

### 与 PR 变更的关联
- **PR 变更触发了该失败**：PR 修改了 `README.md`，使其进入 CI 差异检测列表，从而触发了 appstore 规范的路径校验流程。
- **但失败并非 PR 代码错误导致**：`README.md` 实际路径即为仓库根目录 `/README.md`，PR 未移动或重命名文件，文件位置正确。失效原因为 CI 工具内部的路径格式比对逻辑存在缺陷（相对路径 vs 绝对路径不匹配）。
- 与知识库中模式11（PR #2512 的 `.claude/README.md` 路径问题）相似，均属于 CI appstore 规范检查中的路径校验失败，但两者的具体路径场景不同。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `update.py` 的路径校验逻辑中，差异检测结果 `Difference` 列表给出的路径格式（如 `README.md`，无前导 `/`）与校验规则中期望的路径格式（如 `/README.md`，含前导 `/`）不一致。检查 `update.py` 中路径比对逻辑，统一路径表示格式（统一加 `/` 前缀或统一去掉），确保两者一致。

### 方向 2（置信度: 低）
可能 CI 工具在校验 `README.md` 时，需要确认该文件属于仓库根目录，但其内部路径解析逻辑在解析 diff 时未正确处理根目录文件的路径前缀。需要检查 `update.py` 中 `Difference` 列表的生成逻辑以及后续路径校验时是否对根目录文件做了特殊处理。

## 需要进一步确认的点
1. `update.py:273` 附近的具体校验逻辑——什么条件下会输出 `[Path Error] The expected path should be /README.md`
2. `update.py:356` 附近 `Difference` 列表的生成方式——路径字符串是否始终省略前导 `/`
3. 校验规则（schema/配置）中定义的期望路径格式——是以 `/` 开头还是不以 `/` 开头
4. 同类 PR（仅修改根目录 README.md 的文档 PR）历史上是否有相同的 CI 失败记录
