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
2026-07-14 11:28:17,839-...ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具，非仓库代码）
- 失败原因: CI appstore 发布规范预检工具对 PR 中变更的 `README.md` 执行路径校验时失败。工具报告期望路径为 `/README.md`（带前导 `/`），而实际匹配路径为 `README.md`（无前导 `/`）。但由于两个路径实际指向同一文件，此处不应构成真实的路径合规性问题，更像 CI 工具在路径归一化（normalization）上存在不一致。

### 与 PR 变更的关联
PR 变更仅涉及两个 README 文件（`README.md`、`README.en.md`）中基础镜像 tags 列表的文档更新：新增 24.03-lts-sp4/24.03-lts-sp3/25.09/24.03-lts-sp2 四个条目，并修正 `latest` 指向的版本。PR 未修改任何 Dockerfile、构建脚本、元数据文件或镜像目录结构。CI 失败是 appstore 预检工具对仓库根目录文件触发了不适用的路径校验，与 PR 代码变更内容无关。

## 修复方向

### 方向 1（置信度: 低）
CI 工具 `eulerpublisher` 的 appstore 路径校验逻辑在处理仓库根目录文件时存在路径格式归一化问题——从 git diff 获取的路径为不带前导 `/` 的相对路径，但校验时期望的格式带前导 `/`，导致字符串精确匹配失败。需排查 `update.py` 中路径对比逻辑，确认是否应做归一化处理后再比较，或对根目录文档类文件（非镜像目录下的文件）直接豁免此检查。

### 方向 2（置信度: 低）
PR 源仓库为 fork（`gitcode.com/sunshuang1866/****-docker-images.git`），CI 从 fork 克隆文件和从目标仓库获取期望规范时可能使用不同的路径解析方式，导致类似"仓库根目录下文件的路径前缀处理不一致"的问题。

## 需要进一步确认的点
1. **日志来源核对**：CI 日志上游触发信息为 "PR 3184 [sunshuang1866:fix/3153 -> master]"，与上下文中的 PR #3153 不完全一致（分支名 `fix/3153` 暗示是根据 #3153 衍生的修复分支，但 PR 编号为 3184）。需确认此 CI 日志是否确实对应 PR #3153 的构建。
2. **diff 基准**：CI 日志仅显示 `README.md` 在差异列表中，但 PR diff 明确包含 `README.en.md` 的变更。需确认 CI 计算 git diff 的基准分支是否正确。
3. **路径校验逻辑**：`update.py:273` 中路径校验是精确字符串匹配还是 path normalization 后比较；期望路径 `/README.md` 的来源是硬编码、配置文件还是从 image-list.yml 动态生成；根目录 README 文件在 appstore 规范中的预期行为是什么。
4. **如果该 check 的意图是验证 PR 中变更的每个文件均属于某个已注册的 appstore 镜像条目**，则根目录 `README.md` 未被任何 image-list.yml 条目覆盖，该 check 对根目录文档文件按设计即会失败——此时属于 CI 工具的适用范围问题，非代码 bug。
