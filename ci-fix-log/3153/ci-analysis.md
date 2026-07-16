# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: test-failure
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 纯文档PR路径校验失败
- 新模式症状关键词: Path Error, expected path, README.md, appstore, update.py, specification errors

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,832-INFO: Clone https://gitcode.com/sunshuang1866/****-docker-images.git successfully.
2026-07-14 11:28:17,839-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 (`update.py`) 检测到 PR 变更了仓库根级文件 `README.md`，但该文件不位于任何镜像目录（如 `Bigdata/`、`AI/` 等）内，无法映射到有效的 appstore 路径结构，导致路径校验失败。

### 与 PR 变更的关联
本 PR（#3153）是纯文档更新：仅修改了仓库根目录下的 `README.md` 和 `README.en.md` 两个文件，更新了基础镜像的可用 tag 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 等条目）。PR 未涉及任何 Dockerfile 或镜像构建文件的变更。CI 的 appstore 预检阶段因无法将根级 README.md 匹配到合法的镜像目录路径而失败。

## 修复方向

### 方向 1（置信度: 中）
确认 CI appstore 预检工具对纯文档 PR 的处理策略。如果该工具本身不应该检查根级 README.md（它只应检查镜像目录下的文件），则需要在 CI 脚本中增加过滤逻辑，跳过不属于任何 `{category}/{image}/...` 路径结构的文件。如果根级 README.md 的变更确实需要满足 appstore 规范，则需要确认正确的路径格式要求。

### 方向 2（置信度: 低）
检查 `update.py:356` 附近的 diff 检测逻辑，确认 `Difference` 列表为何只包含 `README.md` 而未包含同样被修改的 `README.en.md`，排除 diff 检测工具存在遗漏或路径处理 bug 的可能性。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 中的路径校验逻辑的具体实现——它期望的文件路径格式是什么，以及它如何处理仓库根级文件。
2. CI 预检工具是否期望纯文档 PR（不含镜像变更）通过 appstore 检查，或这类 PR 应被自动跳过。
3. `Difference` 列表只捕获了 `README.md` 而遗漏了 `README.en.md` 的原因。
