# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级文件路径校验不匹配
- 新模式症状关键词: Path Error, expected path should be, eulerpublisher, appstore

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具（`eulerpublisher`）对 PR 中变更的文件 `README.md` 执行路径校验时，工具获取到的路径为 `README.md`（无前导 `/`），但其内部校验逻辑期望的格式为 `/README.md`（带根路径前导 `/`），路径字符串格式化不匹配导致 FAILURE。`README.md` 实际位于仓库根目录，文件路径本身正确，这是一个 CI 工具链的路径标准化缺陷。

### 与 PR 变更的关联
PR 仅修改了两个根级文档文件——`README.md` 和 `README.en.md`，内容为更新基础镜像可用 Tags 列表（新增 24.03-lts-sp4 / sp3 / sp2、25.09 条目，修正错误 URL）。变更内容本身正确、合法，不涉及任何 Dockerfile、元数据文件或构建逻辑。CI 失败**与 PR 内容质量无关**，是 `eulerpublisher` 工具在解析 git diff 输出的文件路径时缺少前导 `/` 标准化步骤所致。任何修改根级 README 文件的 PR 在当前 CI 环境下均可能触发相同校验失败。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 中路径校验逻辑在比较实际路径与期望路径时未统一添加 `/` 前缀。需在 `update.py` 的路径检查代码中，对从 git diff 提取的文件路径统一添加前导 `/`（或将期望路径去掉前导 `/`），使其与实际文件路径格式一致。这属于 CI 基础设施侧修复，应由 CI 工具维护者处理，Code Fixer 无需修改 Dockerfile 或仓库文件。

### 方向 2（置信度: 低）
若 CI 工具路径校验逻辑本身不可修改，可以考虑在 PR 分支中将 README 更新内容放置到符合 CI 校验预期的路径结构下（但这与文件实际位置矛盾，不具有可操作性）。更合理的方向是等待 CI 工具修复后重建触发。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的路径比较逻辑具体实现，确认路径格式差异的精确位置。
2. 该 CI 检查是否设计上允许对根级 README 文件的修改——若策略上不允许直接修改根级 README，则需了解正确的 README 更新流程。
3. 同类 PR（仅修改根级文档文件）的历史 CI 运行结果，以确认这是新引入的 CI 工具缺陷还是长期存在的已知限制。
