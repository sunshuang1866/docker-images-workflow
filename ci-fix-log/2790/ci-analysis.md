# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: （不适用——已有模式匹配）
- 新模式症状关键词: （不适用）

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对所有 PR 变更文件执行路径规范校验。该 PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档更新），这两个文件位于仓库根层级，不符合 CI 期望的应用镜像目录结构路径格式（如 `{category}/{image}/{version}/{os-version}/Dockerfile`），导致路径校验失败。

### 与 PR 变更的关联
PR 变更仅涉及根目录 `README.md` 和 `README.en.md` 中版本标签的更新（新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 标签条目）。变更内容本身正确无误，但触发了 CI appstore 预检对根目录文件的路径规范校验——该校验预期只对应用镜像子目录下的文件执行，不应作用于仓库根目录的纯文档文件。属于 CI 检查范围的误报。

## 修复方向

### 方向 1（置信度: 中）
CI 预检工具 `update.py` 中的 appstore 路径规范校验逻辑过于宽泛，未排除仓库根目录级别的文档文件（如 `README.md`、`README.en.md`）。修复方向为在 `update.py` 的路径校验逻辑中跳过仓库根目录文件，使其只对应用镜像子目录（`AI/`、`Bigdata/`、`Cloud/` 等）下的文件执行路径检查。

### 方向 2（置信度: 低）
若 CI 工作流允许按 PR 内容类型跳过特定检查步骤，可在 CI pipeline 配置中为纯文档类 PR（仅变更根目录 `*.md` 文件）跳过 appstore 规范预检阶段。

## 需要进一步确认的点
- 当前 CI 的 appstore 预检逻辑是否有文件过滤白名单机制（如排除根目录 `.md` 文件），需要确认 `update.py` 中路径校验的具体实现。
- 类似的历史 PR（仅修改 README 的 PR）是否有相同的 CI 失败记录，需确认这是否为已知的 CI 配置问题。
