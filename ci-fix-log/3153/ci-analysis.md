# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式（与模式11"YAML/元数据文件错误"中的 appstore 路径校验子类相似）
- 新模式标题: 文档变更触发AppStore路径校验
- 新模式症状关键词: Path Error, expected path, /README.md, appstore, specification errors, eulerpublisher update.py

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
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 发布规范校验工具）
- 失败原因: PR #3153 仅修改了仓库根目录的 `README.md` 和 `README.en.md` 两个文档文件（更新基础镜像可用 tags 列表），不涉及任何 Docker 镜像构建文件（Dockerfile、meta.yml、image-info.yml 等）。CI 的 appstore 发布规范预检工具 `update.py` 检测到 `README.md` 发生变更，但该文件位于仓库根路径，不属于任何镜像发布目录的规范结构，因此校验报告的路径检查项失败。

### 与 PR 变更的关联
**PR 变更直接触发了失败，但并非因为变更内容有误**。PR 的文档修改本身是正确的（更新 README 中的 tags 列表），但 CI 的 appstore 发布规范预检期望 PR 中的文件变更位于合法的镜像发布路径（如 `Category/Image/Version/OS/Dockerfile`），根目录的 README.md 不符合该路径模式，导致校验失败。

本质上这是一个纯文档 PR 被 CI 的 appstore 发布检查误报为路径错误的情况——CI 无法区分"纯文档更新 PR"和"应包含镜像发布内容的 PR"。

## 修复方向

### 方向 1（置信度: 中）
该 PR 是纯文档更新，不涉及任何镜像发布。如果合并流程允许纯文档变更跳过 appstore 发布校验，可通过在 CI 中识别 PR 仅包含 `*.md` 文件变更时跳过 `eulerpublisher update.py` 的规范检查。需确认 CI 流程（Jenkins pipeline）中是否有针对文件变更类型的条件判断机制。

### 方向 2（置信度: 低）
如果 CI 工具 `update.py` 的路径校验逻辑存在缺陷——即它将 `README.md`（git diff 中的相对路径）与 `/README.md`（期望的绝对路径）进行比较时因前缀差异导致误判——则需要检查 `update.py` 中路径比对逻辑的实现细节。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的具体校验逻辑——确认 `Path Error` 判定条件是否因路径归一化问题误报。
2. 该 CI 流水线（Jenkins `multiarch/openeuler/trigger/openeuler-docker-images`）是否有针对仅文档变更 PR 的跳过策略。同一 PR 已在日志开头显示 `PR 3184` 编号交叉引用（`PR 3184 [sunshuang1866:fix/3153 -> master] trigger by merge_request`），需确认 PR 编号映射是否正确。
3. `README.en.md` 也在 diff 中但未出现在校验结果表中，需确认是否存在文件过滤白名单。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用——此次错误不涉及正则 patch 外部源文件。
