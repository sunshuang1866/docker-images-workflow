# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 低
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI appstore 发布规范预检对 `README.md` 的路径校验失败，报 `[Path Error] The expected path should be /README.md`。日志中该描述字面含义与实际情况矛盾——PR diff 显示 `README.md` 的实际路径即为仓库根目录下的 `/README.md`（`old_path` 和 `new_path` 均为 `README.md`）。日志不足以确定真正的校验逻辑与期望值之间的偏差。

### 与 PR 变更的关联
PR #2790 仅修改了根目录的 `README.md` 和 `README.en.md` 文件，将"可用镜像 Tags"章节中 `24.03-lts-sp2` 替换为 `24.03-lts-sp3` 作为 latest 标签（URL 也同步更新），并新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 的独立条目。PR 中不包含任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 变更。CI 的 appstore 发布规范预检在扫描到 `README.md` 差异后触发了路径校验，具体校验逻辑无法从日志中推断。

## 修复方向

### 方向 1（置信度: 低）
CI appstore 预检可能对根目录 `README.md` 的修改有特殊的校验规则（如要求同时伴随 image-info.yml / image-list.yml 等发布元数据文件的变更）。如果此假设成立，则需在 PR 中补交对应的发布元数据文件（如为新增的 `25.09` 版本补充对应的 `Base/openeuler/` 下的镜像描述文件），或将根 README.md 的文档变更与镜像发布 PR 分离提交。

### 方向 2（置信度: 低）
CI 工具 `update.py:273` 处的校验逻辑本身存在缺陷，`[Path Error] The expected path should be /README.md` 可能是工具内部路径拼接/解析 bug 产生的误导性报错，实际校验失败原因可能完全不同（如内容格式校验、tag 与已有镜像版本的对应关系校验等）。此情况属于 `infra-error`，与 PR 代码变更无关。

## 需要进一步确认的点
1. `update.py:273` 处 `[Path Error]` 的具体校验逻辑是什么？日志中"Description"显示的"expected path should be /README.md"是否完整覆盖了实际的校验条件？需要查阅 `update.py` 该位置的源码确认校验项。
2. PR 仅修改根目录 README 文档时，appstore 预检的期望行为是什么——是否允许纯文档 PR 通过 CI？如果允许，当前为何失败？
3. 新增的 tag 条目（如 `25.09`、`24.03-lts-sp3`）是否需要在 `Base/openeuler/` 目录下有对应的 image-info.yml 或 image-list.yml 条目？如需要，当前仓库中是否已存在？
