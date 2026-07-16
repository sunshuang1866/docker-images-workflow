# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11（YAML / 元数据文件错误，appstore 路径校验子类）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范检查步骤）
- 失败原因: CI 工具 `eulerpublisher` 对 PR 修改的 `README.md` 执行 appstore 发布规范路径校验时，路径比较逻辑存在归一化不一致问题——实际路径为 `README.md`，期望路径为 `/README.md`（多了一个前导斜杠），导致字符串比较失败。该文件实际位于仓库根目录，在 git diff 及文件系统中的相对路径就是 `README.md`，且恰与期望的 `/README.md` 指代同一文件。属于 CI 基础设施工具的路径比较 bug，非 PR 代码变更问题。

### 与 PR 变更的关联
- **无关联**。PR 变更仅修改了 `README.md` 和 `README.en.md` 中的文档内容（更新基础镜像可用 Tags 列表、新增 24.03-lts-sp4 / 24.03-lts-sp3 / 25.09 三项），未涉及任何 Dockerfile、meta.yml、image-list.yml 或应用镜像文件。CI 检查工具错误地将根级 README 文件纳入 appstore 路径规范校验范围，并因路径比较归一化 bug 导致误报 FAILURE。

## 修复方向

### 方向 1（置信度: 高）
CI 工具侧修复：在 `eulerpublisher/update/container/app/update.py` 的 appstore 路径校验逻辑中，对检测到的文件路径和期望路径做归一化处理（统一添加或去除前导 `/` 后再比较），消除 `README.md` vs `/README.md` 这类表示同一文件但字符串不一致引起的假阳性。此修复应在上游 eulerpublisher 仓库进行，与本 PR 无关。

### 方向 2（置信度: 中）
CI 编排侧修复：若根级 `README.md` 并非 appstore 发布规范检查的目标文件（在项目目录结构中，应用镜像的 README 位于品名/版本/系统版本子目录下，而非仓库根目录），则可调整触发条件，使 CI 仅在 PR 涉及应用镜像子目录（`{category}/{image_name}/`）时才启动 appstore 路径规范检查，避免对纯仓库级文档变更执行无关校验。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径校验的具体实现逻辑——期望路径 `/README.md` 是硬编码默认值，还是根据 PR 变更文件类型动态确定的？如果是硬编码，该 bug 会对所有涉及 README.md 的 PR 产生假阳性。
2. 本仓库根级 README 是否本就不应被 appstore 检查覆盖——检查规范文档中 appstore 路径校验的目标文件范围是否仅为应用镜像子目录下的文件（如 `{category}/{image_name}/{version}/{os_version}/README.md`）。
3. 为何同一 PR 中 `README.en.md` 未被该检查检出——是检查工具只校验 `README.md` 还是 `README.en.md` 也有同样的路径问题但日志中被截断或未展示。

## 修复验证要求
（不适用——本失败为 infra-error，CI 工具路径比较 bug，无需对本 PR 做代码修复。）
