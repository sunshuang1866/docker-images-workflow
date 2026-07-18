# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 文档专用PR路径校验异常
- 新模式症状关键词: appstore releasing specification, Path Error, README.md, expected path, eulerpublisher

## 根因分析

### 直接错误

```
2026-07-14 15:27:59,455-update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,677-update.py[line:222]-INFO: Clone https://gitcode.com/sunshuang1866/****-docker-images.git successfully.
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范校验工具）
- 失败原因: CI 的 `eulerpublisher` 工具对 PR 变更文件进行 appstore 发布规范路径校验，对仓库根目录的 `README.md` 报告 `[Path Error] The expected path should be /README.md`，但该文件确实位于仓库根目录 `/README.md`，错误信息与实际情况矛盾。日志不足以解释为何一个位于预期路径的文件被判定为路径错误。

### 与 PR 变更的关联

本 PR 仅修改了两个文档文件——`README.md` 和 `README.en.md`（中英文 README），内容为更新 "Supported Tags" / "可用镜像的Tags" 章节中的镜像版本列表及链接。PR 未涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 变更。

CI 失败与 PR 的文档内容变更**无直接关联**。失败是 `eulerpublisher` 工具在进行 appstore 发布规范校验时触发的路径检查，该检查似乎无法正确处理仅包含根目录文档变更的 PR——可能因为工具期望被变更的文件属于某个 appstore 镜像发布路径（如 `{category}/{app}/{version}/{os-version}/Dockerfile`），而非仓库根目录的纯文档文件。

## 修复方向

### 方向 1（置信度: 低）
PR 仅修改仓库根目录的 README.md/README.en.md，未涉及任何镜像发布相关文件。若此类纯文档修改 PR 预期不应触发 appstore 发布校验流程，则该 CI 工作流存在配置问题——应在此类 PR 上跳过 `eulerpublisher` 的 appstore 发布规范检查阶段。检查项目 CI 触发条件和流水线编排逻辑。

### 方向 2（置信度: 低）
`eulerpublisher` 工具内部路径校验逻辑可能存在缺陷，对根目录文件的路径格式判断有误（例如解析 `README.md` 时未正确匹配 `/README.md`，或在比较路径时存在首字符 `/` 的不一致）。需排查 `eulerpublisher/update/container/app/update.py` 中路径校验函数的实现逻辑。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 处的 `[Path Error]` 判断逻辑：为何文件路径 `README.md`（根目录）被判定为不符合预期路径 `/README.md`？需获取该 Python 源码中路径匹配逻辑的完整实现。
2. CI 流水线中 appstore 发布规范检查阶段是否对所有 PR 均强制运行（包括纯文档 PR），还是存在白名单/过滤规则。
3. `Difference: ["README.md"]` 中只报告了 `README.md` 变更，但 PR diff 中也包含 `README.en.md` 变更——`eulerpublisher` 工具的 diff 检测逻辑是否忽略了部分文件？这是否与检查异常有关？
4. 该 PR 是否在 fork 仓库 (`sunshuang1866/****-docker-images`) 中缺少某些 CI 工具所依赖的元数据文件（如 `.eulerpublisher.yml` 或类似配置），导致校验脚本在非预期状态下执行。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
本问题不涉及正则 patch 外部源文件，无需额外的上游文件验证。
