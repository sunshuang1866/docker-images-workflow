# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根目录路径格式校验
- 新模式症状关键词: Path Error, expected path, README.md, eulerpublisher, appstore

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489 - update.py[line:356] - INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,839 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具 `update.py` 对 PR 中变更的根目录文件 `README.md` 执行路径校验时，工具内部路径格式为 `README.md`（无前导 `/`），但 appstore 规范要求根目录文件路径格式为 `/README.md`（带前导 `/`），字符串比较不匹配导致检查失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR #3153 为纯文档变更——仅更新 `README.md` 和 `README.en.md` 中基础镜像的 Tags 列表（新增 24.03-lts-sp4/sp3/sp2 和 25.09 等标签），不涉及任何 Dockerfile、meta.yml、image-info.yml 或其他应用镜像构建文件的修改。CI 的 appstore 发布规范检查应针对实际新增/修改的应用镜像目录触发，而不应在纯文档 PR 上执行并报错。

## 修复方向

### 方向 1（置信度: 中）
CI 工具端（`eulerpublisher/update/container/app/update.py`）路径比对逻辑存在缺陷：在处理 git diff 产生的文件路径与 appstore 规范中定义的预期路径格式时，未进行路径格式归一化（normalization）。根目录文件在 git diff 中通常表示为 `README.md`（无前导 `/`），而规范中可能定义为 `/README.md`（带前导 `/`），应在此类预检中统一为绝对路径或相对路径后再比对。

### 方向 2（置信度: 低）
CI 预检流程的触发条件可能存在误判——对纯文档类变更（仅修改 README 文件、不涉及任何镜像构建文件）不应触发 appstore 发布规范检查。可在 `update.py` 的变更文件过滤阶段增加白名单/黑名单逻辑，跳过不涉及镜像构建目录的文档变更。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径比对的具体实现逻辑（第 273 行附近的文件路径处理代码），以确认是否是字符串字面量比较缺少归一化所致。
2. CI 预检流程的触发条件——该 appstore 规范检查是否对所有 PR 无条件执行，还是应有文件变更范围过滤。
3. CI 日志中 Jenkins 上游触发信息提到 `PR 3184 [sunshuang1866:fix/3153 -> master]`，但上下文 PR 编号为 3153，需确认日志是否属于 PR #3153 的同一次失败。

## 修复验证要求
无需在本 PR 提交代码修复。该问题属于 CI 基础设施（`eulerpublisher` 工具）的路径比对逻辑缺陷，应由 CI 平台侧修正。
