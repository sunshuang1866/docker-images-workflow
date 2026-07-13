# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11（YAML / 元数据文件错误——appstore 路径校验）
- 新模式标题: —
- 新模式症状关键词: —

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 脚本，非仓库内文件）
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 变更的 `README.md` 和 `README.en.md` 位于仓库根目录，不符合应用镜像路径规范，判定为路径错误并拒绝通过。

### 与 PR 变更的关联
PR 仅修改了根目录的 `README.md` 和 `README.en.md`（更新可用基础镜像 Tags 列表），属于纯文档修改。CI 的 appstore 路径校验机制将这两个根级文档文件纳入了镜像路径合规检查范围，而它们并非应用镜像目录下的文件，因此被 CI 校验规则错误地标记为失败。**该失败与 PR 的实际内容变更无关**，是 CI 校验范围过宽导致的误报。

## 修复方向

### 方向 1（置信度: 中）
在 CI 校验逻辑（`eulerpublisher/update/container/app/update.py`）中为根级文档文件（如 `README.md`、`README.en.md`）增加豁免规则，使其不被 appstore 镜像路径校验拦截。这需要修改 CI 流水线仓库中的校验脚本，而非此 PR 对应的代码仓库。

### 方向 2（置信度: 低）
若 CI 校验逻辑无法修改，可尝试将本次文档变更从 PR 中分离，通过其他不受 CI 路径校验约束的渠道（如直接合并到主分支）提交文档更新。

## 需要进一步确认的点
- CI 校验工具 `update.py:273` 的路径白名单/豁免逻辑是否可配置，是否已有机制支持跳过根级文档文件的检查。
- 该 appstore 路径校验是否为对所有 PR 的强制检查，还是仅针对特定类型的 PR（如涉及镜像文件变更的 PR）。
- 是否存在绕过该检查的标准方式（如 PR 标签豁免、特殊分支命名等）。
- `eulerpublisher` 工具仓库（`https://gitcode.com/.../eulerpublisher`）的源码地址和修改权限，确认能否在 CI 层面修复此问题。
