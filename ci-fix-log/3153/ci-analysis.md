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
2026-07-16 20:34:19,171-update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI appstore 发布规范校验工具检测到 PR 变更了仓库根目录的 `README.md`，该文件路径不符合应用镜像 appstore 上架的目录结构规范（期望 `/{category}/{image-name}/{version}/{os-version}/README.md` 形式），路径校验失败。

### 与 PR 变更的关联
PR 仅修改了根目录下的 `README.md` 和 `README.en.md` 两个文档文件，更新了基础镜像可用 tags 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2`，并修正了原 `24.03-lts-sp2` 指向错误 SP1 目录的 URL 错误）。这些变更是纯文档修正，不涉及任何应用镜像的新增或修改。CI appstore 规范预检将所有变更文件纳入路径校验范围，根目录 README.md 不属于任何应用镜像的层级目录，因此被标记为路径错误。

## 修复方向

### 方向 1（置信度: 中）
此 PR 为纯文档更新（更新基础镜像 tags 列表），不涉及任何应用镜像的上架。CI appstore 发布规范预检应对此类仅修改根级文档文件的 PR 做放行处理，或 PR 作者应分拆 PR：将基础镜像文档更新与应用镜像上架分开提交，避免根级 README 变更触发 appstore 路径校验。

### 方向 2（置信度: 低）
若 CI 无法区分文档 PR 与应用镜像 PR，可考虑将根级 README.md 的变更排除在 appstore 路径校验范围之外（在 `update.py` 中添加白名单过滤逻辑），使根级文档文件的修改不再触发路径校验失败。

## 需要进一步确认的点
1. PR #3153 是否与其他 PR（如日志中提到的 PR #3184，分支名 `sunshuang1866:fix/3153`）有关联？PR #3184 是否整合了 #3153 的修改并附带了其他应用镜像变更，从而触发了 appstore 路径校验？
2. CI appstore 规范预检工具 `update.py` 中路径校验的具体逻辑：它对文件路径的期望规则是什么？`[Path Error] The expected path should be /README.md` 这个提示的具体含义是期望 root 路径还是某种模板格式？
3. 同仓库中是否有其他仅修改根级文档文件的 PR 也曾遇到相同的 CI 失败？如有，则可为模式11 补充新案例。

## 修复验证要求
（不适用——本报告涉及的是 CI 校验逻辑/PR 拆分策略问题，不涉及正则 patch 外部源文件。）
