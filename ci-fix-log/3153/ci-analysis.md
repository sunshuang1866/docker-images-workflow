# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py:273`）
- 失败原因: CI appstore 路径校验工具对仓库根目录下的 `README.md` 报出 `[Path Error]`，声称期望路径为 `/README.md`。但 PR 变更的 `README.md` 确实位于仓库根目录（等同于 `/README.md`），路径本身正确。该失败与 PR 代码变更无关，属于 CI 工具路径校验逻辑缺陷。

### 与 PR 变更的关联
**无关联。** PR #3153 仅修改了 `README.md` 和 `README.en.md` 的文档内容（更新基础镜像可用 Tags 列表），未涉及任何 Dockerfile、元数据文件或构建逻辑的变更。CI 失败发生在 appstore 发布规范预检阶段，该检查将根目录的 `README.md` 误判为路径错误——此行为与 PR 的具体内容无关。

## 修复方向

### 方向 1（置信度: 低）
CI appstore 路径校验工具可能存在路径格式比对缺陷（如未对 `README.md` 与 `/README.md` 做归一化处理，或工具运行工作目录与预期不一致导致相对路径/绝对路径混用）。需排查 `eulerpublisher/update/container/app/update.py` 中路径校验逻辑，确认其在处理仓库根目录文件时是否存在字符串比对遗漏。

### 方向 2（置信度: 低）
CI 工具设计上可能仅预期处理镜像子目录内的文件（如 `AI/xxx/Dockerfile`），对仓库根目录文件（`/README.md`）的变更缺乏正确的校验处理分支，导致误报。需确认该 appstore 预检工具是否应跳过根目录非镜像文件的检查。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径校验的具体实现逻辑——对比路径时是否进行了归一化（如去除前导 `/` 或添加前导 `/`）。
2. 同一 CI 流水线中是否有其他 PR（仅包含根目录文件变更的 PR）遇到同样的 `[Path Error]`——以判断这是本次运行的特例还是 CI 工具的已知长期缺陷。
3. CI 工具运行时的工作目录（`cwd`）是什么——如果工具从非仓库根目录执行，则 `README.md` 的检测路径可能不包含前导 `/`，导致与 `/README.md` 的期望值不匹配。
4. 该 appstore 预检是否设计为只校验镜像子目录内的文件——如果是，则根目录 README.md 变更应当被自动豁免而非报错。

## 修复验证要求
（无需填写——该失败为 CI 基础设施问题，不涉及代码修复。）
