# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

以及 diff 检测日志：
```
INFO: Difference: [
    "README.en.md",
    "README.md"
]
```

### 根因定位
- 失败位置: CI appstore 发布规范预检（`eulerpublisher/update/container/app/update.py:273`）
- 失败原因: CI appstore 发布规范检查对所有 PR 变更文件进行路径校验，要求变更文件位于应用镜像的标准目录结构（如 `{category}/{app}/{version}/Dockerfile`）内。此 PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`，两个文件均不在任何应用镜像目录下，因此被判定为路径不合规。

### 与 PR 变更的关联
PR 变更仅涉及根级 `README.md` 和 `README.en.md` 中基础镜像标签列表的文档更新（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09` 和 `24.03-lts-sp2` 的链接，修正 latest 标签指向）。变更本身是合法的文档维护操作，但由于触发了 CI 的 appstore 发布规范预检，而该检查要求所有变更文件必须符合应用镜像目录结构，导致失败。

值得注意的是，`README.md` 的错误描述为"expected path should be /README.md"——而其本身即位于 `/README.md`。这表明 checker 的错误消息可能与实际校验逻辑不完全一致：`/README.md` 可能是 checker 对所有非应用镜像目录下 `.md` 文件的默认/回退期望路径，而非真正的目标路径。

## 修复方向

### 方向 1（置信度: 中）
此 PR 是纯文档 PR，不涉及任何应用镜像变更。CI appstore 发布规范预检可能需要对纯文档 PR 进行豁免处理——即当 diff 中仅包含仓库根级文档文件且无任何应用镜像目录变更时，跳过路径校验。需要在 CI 流水线或 `update.py` 中增加此类豁免逻辑。

### 方向 2（置信度: 低）
若 CI 设计意图是所有 PR（包括文档 PR）都必须关联一个应用镜像变更，则需要在本次 PR 中补入一个合法的应用镜像目录变更（如补充某个应用镜像的 README 或 meta.yml），以满足 appstore 预检要求。但此举会引入与 PR 标题意图无关的变更，不建议采用。

## 需要进一步确认的点
1. `update.py:273` 的具体路径校验逻辑——需要确认 checker 是如何判断"期望路径"的，以及为什么 `/README.md` 本身也会报错。可能该 checker 存在 bug，或者其校验逻辑是将根级 `.md` 文件统一视为不合规。
2. CI 流水线是否有配置项可以跳过 appstore 预检（例如通过 PR 标签 `skip-appstore-check` 或类似机制）。
3. 历史 case PR #2512（模式11 中 `.claude/README.md` 路径校验失败）的最终处理方式是否有参考价值。

## 修复验证要求
不涉及正则 patch 外部源文件的操作，无需特殊验证步骤。
