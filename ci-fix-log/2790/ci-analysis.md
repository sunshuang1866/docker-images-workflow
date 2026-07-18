# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根目录README路径校验
- 新模式症状关键词: Path Error, The expected path should be, update.py, appstore, README.md

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR:
There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 预检脚本）
- 失败原因: CI 的 appstore 发布规范预检工具 `update.py` 检测到 PR 变更中包含根目录下的 `README.md`，对该文件执行路径校验时报告 `[Path Error] The expected path should be /README.md`，导致预检阶段失败。PR 仅修改了仓库根目录的两个文档文件（`README.md` 和 `README.en.md`，更新了基础镜像 Tags 列表），未涉及任何 Dockerfile、meta.yml 或 image-info.yml 等应用镜像发布所需的文件。

### 与 PR 变更的关联
PR #2790 仅修改了 `README.md` 和 `README.en.md`（更新 openEuler 基础镜像的 Tags 列表，添加了 24.03-lts-sp3、25.09 等新标签，并修复了原有行中 24.03-lts-sp2 的 URL 指向 SP1 目录的旧错误）。CI 的 `update.py` 预检工具在解析 diff 后，将 `README.md` 列为变更文件（日志 `Difference: ["README.md"]`），随后对其进行 appstore 发布规范路径校验，校验未通过导致整体预检失败。该失败与 PR 对文档内容的修改**有关联**——是 README.md 文件本身的变更触发了预检工具的路径检查逻辑，但失败的直接原因是预检工具对根目录 README.md 的路径解析或校验规则，而非 README.md 的内容错误。

## 修复方向

### 方向 1（置信度: 中）
CI 预检工具 `update.py` 在检查变更文件时，可能以某种方式将根目录 `README.md` 视为需要符合应用镜像目录规范的路径，与期望的路径格式 `/README.md`（带绝对路径前缀）不匹配。需检查 `update.py` 中路径规范化逻辑——例如在其路径对比逻辑中为根级文件统一添加或移除前导 `/`，使 `README.md` 与 `/README.md` 能正确匹配。此方向的依据是：错误描述恰为 "The expected path should be /README.md"，而 git diff 输出的文件路径不含前导 `/`。

### 方向 2（置信度: 低）
PR 中 `README.md` 的内容有事实错误——`24.03-lts-sp3` 标签在 diff 中出现了**两次**（一次作为 `[24.03-lts-sp3, 24.03, latest]` 行新增，另一次作为独立 `[24.03-lts-sp3]` 行新增），但 CI 报错是明确的路径校验错误（`Path Error`）而非内容校验错误，因此内容重复更可能是附带问题而非根因。

## 需要进一步确认的点
1. **`update.py` 路径校验逻辑**：需查阅 `eulerpublisher/update/container/app/update.py` 中第 273 行附近的路径校验代码，确认该工具对根目录文件（如 `README.md`）的路径解析逻辑以及期望的路径格式。
2. **CI 预检工具的触发范围**：确认 `update.py` 是否应当对所有 PR 运行（包括纯文档 PR），还是只应针对涉及应用镜像目录的 PR。该 PR 仅修改了仓库根目录的 README 文件，不涉及任何应用镜像发布变更。
3. **与模式 11（YAML/元数据文件错误）的异同**：历史模式 11 中记载了多例 CI path 校验失败案例（如 `.claude/agents/README.md` 路径不符合规范），当时的修复方向是移动文件到正确位置。但本 PR 的 README.md 是仓库根目录的项目级文档，不存在"移动到正确路径"的修复方向——需确认 `update.py` 是否错误地将所有变更文件都纳入 appstore 路径规范校验。

## 修复验证要求
若修复方向 1 涉及修改 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑，则 code-fixer 必须：
- 确认 `update.py` 路径校验代码中对根目录文件（`README.md`、`README.en.md` 等）的处理分支是否缺失或存在 bug
- 验证修复后，仅修改仓库根目录 README 文件的 PR 不再被预检工具误判为路径错误
- 如修复涉及对 `eulerpublisher` 仓库（而非本仓库）的修改，需在对应的 CI 编排配置中更新 `eulerpublisher` 的引用版本
