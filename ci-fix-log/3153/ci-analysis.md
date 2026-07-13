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
2026-07-12 15:33:08,211-/home/jenkins/.../eulerpublisher/update/container/app/update.py[line:356]-INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-07-12 15:33:13,075-/home/jenkins/.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范校验工具）
- 失败原因: CI 的 `eulerpublisher` 工具对 PR 变更文件执行 appstore 发布规范路径校验，PR 仅修改了仓库根目录下的两份文档文件（`README.md`、`README.en.md`），这两个文件不在 CI 期望的 appstore 镜像发布目录路径（如 `{Category}/{Image}/{Version}/{OSVersion}/`）下，路径校验未通过。

### 与 PR 变更的关联
PR 变更内容为纯文档更新：在 README.md 和 README.en.md 中增补基础镜像可用 tag 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目）。这些变更本身无误，但触及了 CI appstore 发布规范检查——该检查要求所有变更文件落在有效的镜像构建目录层级下，根目录 README 文件不属于 appstore 规范允许的路径范围，因此被拒绝。失败与 PR 的文档内容无关，而是 CI 检查范围与 PR 变更类型不匹配。

## 修复方向

### 方向 1（置信度: 中）
根目录 README 文件的纯文档更新不应触发 appstore 发布规范校验。需要确认 CI 流水线是否应为此类纯文档 PR 跳过 `eulerpublisher` 的路径校验步骤，或在 `eulerpublisher` 工具中为根目录文档文件（`/README.md`、`/README.en.md` 等）添加白名单例外逻辑。

### 方向 2（置信度: 低）
若 CI 策略要求所有 PR 文件必须通过 appstore 路径校验且不允许例外，则根目录 README 的更新可能需通过其他渠道完成（如绕过本仓库 CI 流水线的直接合并，或通过专门的文档仓库管理）。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现——为何 `/README.md` 对文件 `README.md` 自身仍判定为 FAILURE。
2. CI 流水线配置中是否有针对纯文档 PR 的跳过策略（如检测到 PR 仅修改 `*.md` 文件时跳过 appstore 路径校验）。
3. 该仓库是否允许合并仅修改根目录 README 文件的 PR，或文档更新是否有独立的发布流程。
