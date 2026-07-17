# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 根README路径误检
- 新模式症状关键词: appstore, Path Error, README.md, expected path, 发布规范

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-... -ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI appstore 发布规范预检阶段（`eulerpublisher/update/container/app/update.py:273`）
- 失败原因: CI 的 appstore 发布规范检查工具对仓库根目录的 `README.md` 文件进行了路径校验，错误信息称"期望路径应为 `/README.md`"，但该文件实际就在 `/README.md` 位置，存在自相矛盾。仓库根目录的 `README.md` 是项目级文档，并非 appstore 镜像发布的范畴，CI 工具应将其排除在校验范围之外。该失败与 PR 内容无关。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 两个文档文件，更新了 openEuler LTS 版本标签信息（新增 24.03-lts-sp3、25.09、24.03-lts-sp2 标签，将 latest 指向从 SP1 改为 SP3），属于纯文档变更。CI 的 appstore 路径校验工具误将根目录 `README.md`（项目整体说明文档）当作需上架 appstore 的镜像文件进行校验，导致路径检查失败。该失败与 PR 改动无因果关系，任何修改根目录 `README.md` 的 PR 都可能触发相同失败。

## 修复方向

### 方向 1（置信度: 低）
CI appstore 发布规范检查工具（`eulerpublisher` 的 `update.py`）应将项目根目录的 `README.md` / `README.en.md` 从文件变更检查范围中排除——这些文件是仓库级别的项目文档，不涉及应用镜像上架。此修复需由 CI 基础设施团队在 `eulerpublisher` 工具侧完成，PR 作者无需修改任何代码。

### 方向 2（置信度: 低）
若 CI 工具的路径校验逻辑本身存在 bug（期望路径与实际路径一致却仍报 FAILURE），需检查 `update.py:273` 附近的正则/路径匹配逻辑是否存在代码缺陷。

## 需要进一步确认的点
- `eulerpublisher` 工具的 `update.py` 中，appstore 发布规范检查的路径过滤逻辑是什么：是否将仓库根目录的 `README.md` 纳入了检查范围？若纳入，是预期行为还是 bug？
- 错误信息"expected path should be /README.md"与实际路径 `/README.md` 一致却报 FAILURE 的原因——是路径判断逻辑有误，还是错误消息中的路径与实际校验路径不一致？
- 同 PR 中 `README.en.md` 也被修改，但 CI 差异检测仅列出了 `README.md`，需确认 `README.en.md` 是否被正确忽略了，以及两者处理逻辑是否一致。
- 该 CI 失败是否为当前 CI 环境中的已知问题（是否存在类似 case 表明修改根 README 总是触发此误报）？

## 修复验证要求
该失败为 infra-error，置信度为"低"，**code-fixer 不应执行任何代码修改**。如果 CI 团队确认是 `eulerpublisher` 工具的 bug 并修复后，需重新触发 CI 流水线验证该 PR 能否通过 appstore 发布规范检查。
