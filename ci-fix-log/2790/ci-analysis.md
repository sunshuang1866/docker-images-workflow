# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（松散匹配）
- 新模式标题: 文档PR误触发appstore校验
- 新模式症状关键词: Path Error, The expected path should be, appstore, README.md, 根级文件

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455 - INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对 PR 中的变更文件执行路径校验，期望所有变更文件位于符合 Docker 镜像发布规范的目录路径下，但该 PR 仅修改了仓库根级的 `README.md` 和 `README.en.md` 文档文件，这些文件不匹配任何镜像发布路径模板，导致路径校验失败。

### 与 PR 变更的关联
PR 变更仅涉及两个根级文档文件（`README.md`、`README.en.md`），内容是更新基础镜像的 Tags 列表（新增 `24.03-lts-sp3`、`25.09` 等版本条目）。这些变更属于纯文档维护，不涉及任何 Dockerfile、meta.yml、image-list.yml 或镜像构建相关文件。CI appstore 预检工具无法将根级文档文件映射到合法的镜像发布路径，从而报错。因此该失败是 CI 校验逻辑对文档 PR 过度扩展所致，PR 变更本身无代码或规范问题。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 预检规则应跳过仓库根级文件（`/README.md`、`/README.en.md`、`/LICENSE` 等），仅对镜像目录内的文件执行路径校验。若 `update.py` 中有白名单或排除逻辑，需将根级文档文件加入排除列表；若 CI 工具链由独立仓库维护，需联系 CI 团队修改校验规则。

### 方向 2（置信度: 低）
检查 `eulerpublisher` 工具的 `update.py` 第 273 行附近的路径校验逻辑，确认其是否对"仅包含根级文件变更"的 PR 存在 corner case 处理缺陷——当前输出 `The expected path should be /README.md` 语义模糊，可能是校验逻辑将空路径或根路径误判为非法。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 270-280 行的具体路径校验逻辑——需要确认其如何判断合法路径以及是否有文件排除机制。
2. CI 是否对所有 PR（包括纯文档更新）强制要求通过 appstore 发布规范预检——若是，则需在 CI 配置层面或校验工具代码层面对根级文档文件做豁免处理。
3. 该仓库之前是否有纯文档 PR 成功通过 CI 的记录——若有，则说明当前失败可能是校验工具的回归缺陷。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。该失败不涉及对第三方/上游源文件的正则 patch。
