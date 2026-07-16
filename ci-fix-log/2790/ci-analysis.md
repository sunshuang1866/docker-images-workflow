# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```
```
2026-07-14 15:27:59,455-INFO: Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）检测到 PR 变更了根目录下的 `README.md`，在执行路径校验时将 `/README.md` 视为不符合预期规范的路径，判定为 `[Path Error]` 并导致构建失败。PR 仅修改了根级文档文件 `README.en.md` 和 `README.md`（更新 Tags 列表），并未涉及任何 Dockerfile、meta.yml 或 image-info.yml 等镜像制品文件。

### 与 PR 变更的关联
PR #2790 的变更仅涉及两个根级 README 文件的文档内容更新（新增 24.03-lts-sp3、25.09 等 Tags 条目）。变更内容本身是正确的（更新 Tags 别名和对应 URL），不涉及任何 Docker 镜像构建逻辑。CI 失败的直接原因是 appstore 发布规范预检工具将该文档变更误判为镜像发布变更，并对根级 `README.md` 执行了不适用的路径校验。**该失败与 PR 的文档改动内容无关，属于 CI 校验流程对纯文档 PR 的误报。**

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 发布规范预检（`update.py` 第 273 行附近）在检测到 `README.md` 变更后，将其纳入镜像发布路径校验流程。对于纯文档 PR（仅修改根级 README 而无任何 `{场景}/{镜像}/{版本}/{OS}/Dockerfile` 路径下的文件变更），该预检不应触发路径校验。可能的处理方式：
- 在 `update.py` 的 diff 检测逻辑中，过滤掉仅变更根级 README/README.en.md 且无任何镜像目录文件变更的 PR，跳过 appstore 发布规范检查。
- 或者在路径校验规则中，将根级 `/README.md` 和 `/README.en.md` 加入白名单/豁免列表，不参与 appstore 发布规范校验。

### 方向 2（置信度: 低）
本 PR 可能不完全符合正常镜像 PR 的格式要求（如缺少 `meta.yml` 或 `image-info.yml` 条目变更），导致 CI 在仅检测到 `README.md` 变更时无法匹配到任何镜像发布条目，进而触发路径错误。但这与 PR 的实际意图（纯文档更新）不一致，此方向的置信度较低。

## 需要进一步确认的点
1. 确认 `update.py` 第 273 行附近的具体校验逻辑：路径校验是针对所有 diff 文件还是仅针对特定类型的文件（如 image-info.yml、meta.yml、Dockerfile）。
2. 确认根级 `README.md` 是否有对应的 `image-list.yml` 条目或 meta 配置，导致 CI 预期该文件应遵循镜像发布路径规范（如 `{image-version}/{os-version}/README.md`）。
3. 确认是否其他仅修改根级 README 的 PR 也会触发同样失败，以判断这是偶发问题还是已知的系统性问题。

## 修复验证要求
（不适用——此失败为 CI 基础设施导致的误报，不涉及对外部源文件的 patch 或正则修改。）
