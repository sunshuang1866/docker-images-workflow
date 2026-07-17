# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验误报
- 新模式症状关键词: Path Error, expected path should be, appstore, README.md, release specification

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051 ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检步骤）
- 失败原因: CI 的 appstore 发布规范预检工具检测到仓库根目录 `README.md` 发生了变更，对其执行路径格式校验时判定路径不符合预期（期望 `/README.md`）。该检查工具设计用于验证应用镜像目录结构（`{category}/{image-name}/{version}/{os-version}/...`），对仓库根级文件的路径解析存在兼容性问题。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #3153 仅修改了两份根级文档的**内容**（READM.md 和 README.en.md 中基础镜像 Tags 列表），未新增/删除/移动任何文件，未修改任何 Dockerfile、meta.yml、image-list.yml 或构建脚本。该失败是 CI 工具（eulerpublisher appstore 预检）在扫描变更文件时，将根级文档误纳入应用镜像发布规范校验流程导致的误报，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施团队排查 eulerpublisher 的 appstore 发布规范预检逻辑。该预检应跳过仓库根目录的非应用镜像文件（如 `README.md`、`README.en.md`、`.github/` 等），仅对 `{category}/{image-name}/{version}/{os-version}/` 路径下的文件执行应用镜像路径格式校验。

## 需要进一步确认的点
- eulerpublisher `update.py` 中变更文件检测逻辑是否按文件路径做了过滤（排除根级文档），还是对所有 git diff 文件无差别执行 appstore 路径校验。
- 是否有其他同类纯文档 PR 也触发了相同的 appstore 路径校验失败（可对照模式11 中 `PR #2512` 的 `.claude/` 路径案例，虽然场景不同但都属于 CI 预检工具对非应用镜像文件路径的误判）。
