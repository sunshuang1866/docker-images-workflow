# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11 (YAML/元数据文件错误)
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: 应用商店发布校验工具对仓库根目录的 README 文件执行了路径校验，判定 README.md 和 README.en.md 的路径不符合预期（预期路径为 `/README.md`）。

### 与 PR 变更的关联
PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md` 两个文档文件，未涉及任何镜像 Dockerfile 或 image-list.yml 的改动。CI 的 update.py 脚本检测到 diff 中包含这两个文件后，触发了应用商店发布规范的路径校验逻辑。校验逻辑报告两者路径错误，但二者情况不同：

1. **README.md**：该文件实际路径即为 `./README.md`，与校验工具报出的"预期路径 `/README.md`"一致，属于**误报**——校验工具可能使用了错误的基准路径或比较逻辑。
2. **README.en.md**：该文件在仓库根目录，但应用商店发布规范可能不期望根目录存在英文版 README（允许的预期路径仅为 `/README.md`），此失败有一定合理性但信息不足。

由于两个文件输出相同的错误信息，更可能的情况是校验工具对所有非镜像子目录内的 README 文件存在路径判断缺陷。

## 修复方向

### 方向 1 (置信度: 中)
检查 `eulerpublisher/update/container/app/update.py` 中路径校验逻辑对仓库根目录 README 文件的处理。根目录的 `README.md` 应被校验工具视为合法的应用商店路径 (`/README.md`)，而非报告错误。可能的修复包括：在校验规则中将根目录 README 文件加入白名单，或修正路径比较时的工作目录基准。

### 方向 2 (置信度: 低)
确认 `README.en.md` 是否为应用商店发布规范的合法文件。若规范预期仅有 `README.md`，则 PR 中对 `README.en.md` 的修改不应触发发布校验（或应跳过该校验）。可在 update.py 中增加文件类型过滤，对已知非应用商店发布范围的文件跳过路径校验。

## 需要进一步确认的点
- `update.py` 中路径校验逻辑的具体实现：期望路径 `/README.md` 的基准目录是什么，是否有前缀拼接或路径规范化问题。
- 历史 PR 中对根目录 README 的纯文档修改是否同样触发过此校验（确认是否为长期存在的已知问题）。
- `README.en.md` 在应用商店发布规范中是否属于受管控的文件范围。
- 该 CI 检查步骤是否为必要门禁（blocking），以及是否有跳过/豁免机制。

## 修复验证要求
- 重新提交仅修改根目录 README 文件的 PR，验证应用商店路径校验步骤通过。
- 分别测试仅修改 `README.md` 和仅修改 `README.en.md` 的场景，确认两者的处理逻辑一致且正确。
