# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: test-failure
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档路径格式校验
- 新模式症状关键词: Path Error, expected path, /README.md, update.py, eulerpublisher, appstore, release specification

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 发布规范校验脚本）
- 失败原因: CI 在检测到 `README.md` 被修改后，运行发布规范（appstore release specification）校验，发现 `README.md` 中某处路径格式不符合预期——校验器期望路径以 `/` 开头（如 `/README.md` 的格式），但 README 中存在未以 `/` 开头的路径引用（如 `存放路径：Base/openeuler/Dockerfile`）。

### 与 PR 变更的关联
**PR 变更本身不直接触发此失败。** PR #3153 仅修改了 `README.md` 和 `README.en.md` 中"可用镜像 Tags"列表的内容——更新条目、添加新 tag——属于纯文档更新。失败的根因是 CI 发布规范校验脚本对 `README.md` 进行全量校验时，发现了 README 中**原本就存在**的路径格式问题（如 `Base/openeuler/Dockerfile` 缺少前导 `/`）。由于 `README.md` 被 PR 修改，触发了全量重新校验，这个预存问题才暴露出来。

## 修复方向

### 方向 1（置信度: 中）
检查 README.md 中所有路径引用（如"存放路径"章节的 `Base/openeuler/Dockerfile` 等），确认 CI 校验器所期望的路径格式是否为绝对路径（以 `/` 开头），若确认为格式问题，需统一路径格式使之符合 appstore 发布规范要求。

### 方向 2（置信度: 低）
CI 校验脚本 `eulerpublisher/update/container/app/update.py` 本身可能存在正则或校验逻辑缺陷，对合法的相对路径误报为错误。若方向 1 确认 README 中的路径实际上符合规范，则需要排查该校验脚本的实现逻辑。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中 `[Path Error] The expected path should be /README.md` 这条校验规则的具体实现——具体在检查 README.md 中的哪个字段/哪一行，以及期望的格式到底是什么。
2. README.md 中"存放路径"等章节的历史内容——该路径 `Base/openeuler/Dockerfile` 是否在之前的 CI 运行中也曾引发过此问题，还是本次 CI 首次运行该校验规则。
3. 该发布规范校验是否是新增的 CI 检查项，以及其预期的路径格式文档说明。

## 修复验证要求
由于置信度为"中"，code-fixer 在提交修复前必须：
1. 获取 `eulerpublisher/update/container/app/update.py` 源码，确认 `line:273` 附近的校验逻辑和报错上下文。
2. 从 PR 作者仓库 (`sunshuang1866/openeuler-docker-images`) 的 `fix/3153` 分支拉取 `README.md`，确认触发校验失败的具体内容行。
3. 若修复涉及修改 README.md 中的路径格式，需验证新格式是否通过该 appstore 发布规范校验的全部检查项。
