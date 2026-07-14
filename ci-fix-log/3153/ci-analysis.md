# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-12 15:33:08,211-...-INFO: Difference: [
    "README.en.md",
    "README.md"
]
...
2026-07-12 15:33:13,075-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检逻辑）
- 失败原因: CI 的 appstore 发布规范预检工具将 `README.md` 和 `README.en.md` 两个仓库根级文档文件的变更纳入了 appstore 镜像路径校验流程。这两个文件不在 appstore 镜像目录结构（`{分类}/{镜像}/{版本}/{系统版本}/`）中，校验工具无法将它们映射到合法镜像路径，因此判定为路径错误（Path Error）。

### 与 PR 变更的关联
- **PR 直接触发了失败，但 PR 变更本身是合法的**。PR 仅修改了 `README.md` 和 `README.en.md` 中基础镜像可用 tags 列表，属于纯文档更新，不含任何 Dockerfile、meta.yml、image-list.yml 等应用镜像相关文件变更。
- **根因在 CI 流水线设计**：CI 对所有 PR（包括纯文档 PR）均运行 appstore 发布规范预检，该检查只接受符合镜像目录结构的文件路径。仓库根级的 README 文档文件不属于 appstore 镜像范畴，却无豁免机制，导致误报路径错误。

## 修复方向

### 方向 1（置信度: 高）
CI 流水线应跳过对纯文档 PR 的 appstore 发布规范预检，或在 eulerpublisher 工具中为仓库根级文件（如 `README.md`、`README.en.md`、`LICENSE` 等）增设白名单/豁免逻辑。此类文件不属于 appstore 镜像发布范畴，不应参与镜像路径校验。

### 方向 2（置信度: 中）
若 CI 流水线端暂无法改动，可在 eulerpublisher 的 `update.py` 路径校验方法中增加判断：当变更文件位于仓库根目录且属于已知文档文件（`README.md`、`README.en.md`）时，跳过 appstore 路径校验或直接返回通过。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中路径校验的具体实现逻辑（`update.py:222-273` 之间的代码），以确定白名单/豁免机制的插入点。
- CI 流水线配置（Jenkinsfile 或等价 pipeline 描述文件），确认是否存在按变更文件类型跳过 appstore 检查的机制（若无，需新增）。
- 确认 PR #2512（`.claude/README.md` 同类路径错误）的最终修复方式，作为参考。

## 修复验证要求
（不涉及正则 patch 外部源文件，无需填写）
