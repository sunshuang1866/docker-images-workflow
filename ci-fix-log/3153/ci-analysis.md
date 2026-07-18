# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (无)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-/.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: CI appstore 发布规范预检阶段，`eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 检测到 `README.md` 发生变更后，appstore 发布规范预检工具对该文件执行路径校验，报告"预期路径应为 /README.md"，判定路径不匹配。`README.md` 实际位于仓库根目录（即 `/README.md`），日志无法进一步解释为何校验工具认为路径不符合预期。

### 与 PR 变更的关联
直接关联。PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（更新基础镜像可用 tag 列表：将 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`，新增 `24.03-lts-sp3`、`25.09` 条目）。CI 的 diff 检测发现 `README.md` 变更后，将其纳入 appstore 发布规范检查范围并报路径错误。该 PR 为纯文档更新，未涉及任何镜像 Dockerfile、meta.yml 或 image-info.yml 的新增或修改。

## 修复方向

### 方向 1（置信度: 中）
该检查可能为误报—PR 仅修改了根目录纯文档 README.md，不涉及 appstore 镜像发布。若 CI 平台的 appstore 规范检查允许对纯文档类文件跳过校验，可通过配置豁免根目录 `README.md` / `README.en.md` 的 appstore 路径检查。或者确认 CI 工具中对路径的对比方式是否存在绝对路径与相对路径不一致的问题（`README.md` vs `/README.md`）。

## 需要进一步确认的点
1. CI appstore 规范检查工具（`update.py`）对 `README.md` 执行路径校验的具体逻辑：文件实际位于 `/README.md`，为何被判定为路径不符合预期？
2. 该 appstore 规范检查是否应当在纯文档 PR（无镜像发布内容）上跳过？
3. 历史同类 PR（如模式19 中 PR #2308：`AI/diskann/README.md` 纯文档修正）是如何通过该检查的，是否有配置差异？

## 修复验证要求
（无——本报告不涉及正则 patch 外部源文件）
