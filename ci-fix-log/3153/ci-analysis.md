# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具内部）
- 失败原因: CI 的 appstore 发布规范校验工具在比较变更文件路径时，将 git diff 中的相对路径 `README.md` 与预期绝对路径格式 `/README.md` 做字符串比对，因缺少前导 `/` 判定为"路径错误"。PR 实际变更仅为 `README.md` 和 `README.en.md` 中的文档标签列表更新，`README.md` 确实位于仓库根目录（即 `/README.md`），这是 CI 工具的路径规范化缺陷（false positive），并非 PR 代码存在问题。

### 与 PR 变更的关联
PR 变更仅修改了 `README.md` 和 `README.en.md` 中"可用镜像的 Tags"列表（新增 4 条标签记录、调整 1 条），属于纯文档更新。CI 失败源于下游 x86-64 构建 job 中的 `eulerpublisher` 工具执行 appstore 路径规范预检时对仓库根目录文件的路径格式校验过于严格（要求绝对路径 `/README.md`，但收到相对路径 `README.md`）。该失败与 PR 的文档改动内容本身无关，属于 CI 基础设施工具的逻辑问题。

## 修复方向

### 方向 1（置信度: 高）
CI 工具 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑存在缺陷：对仓库根目录文件（如 `README.md`）进行 appstore 路径规范检查时，未将相对路径标准化为绝对路径格式（加前导 `/`）。需修复 `update.py` 中的路径比较逻辑，在比对前对变更文件路径做规范化处理（如对根目录文件自动补 `/` 前缀）。注意：此修复位于 CI 工具仓库（`eulerpublisher`），不在当前 Docker 镜像仓库中。

### 方向 2（置信度: 低）
如果该路径校验是 appstore 上架规范的真实要求（即必须使用绝对路径引用根目录文件），则可能需要在 PR 提交时确保 diff 中的文件路径格式满足 CI 工具所期望的格式。但从 git diff 的标准行为来看，根目录文件不可能以 `/` 开头的形式出现在 diff 中，因此这个可能性极低。

## 需要进一步确认的点
1. `eulerpublisher` 工具仓库中 `update/container/app/update.py:273` 附近的具体路径比对逻辑实现，确认是字符串严格相等比较还是已包含路径规范化步骤。
2. 该 CI 检查是否对仓库中所有根目录文件（非 README 的其他文件）也会触发同类误报，以判断问题影响范围。
3. 是否有其他 PR 曾成功通过该 appstore 路径检查但同样修改了根目录文件（排除有特殊豁免规则的 case）。
