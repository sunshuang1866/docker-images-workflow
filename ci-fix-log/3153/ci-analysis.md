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
2026-07-16 20:34:43,051-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

CI 检测到仅 `README.md` 有变更：
```
INFO: Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检（`eulerpublisher` 工具）对 PR 中变更的 `README.md` 进行路径校验时失败。该检查期望变更为符合 appstore 上架规范的文件路径结构，而 PR 仅修改了仓库根目录级别的 README 文件（`README.md` / `README.en.md`），未伴随任何应用镜像的 Dockerfile 或元数据文件变更，不被 appstore 发布工作流识别为合法发布路径。

### 与 PR 变更的关联
**PR 变更直接触发了此失败。** PR 的 diff 仅修改了两个文件：
- `README.md` — 更新基础镜像可用 tags 列表（新增 sp4/sp3/sp2/25.09）
- `README.en.md` — 同上

这两个文件是仓库根级的文档文件。CI 工具 `eulerpublisher` 的 appstore 发布预检在扫描到 PR 有文件变更后，会校验变更文件是否符合 appstore 上架路径规范。由于根级 README 的文件变更不符合"应用镜像发布"的路径模式（期望路径为 `{分类}/{镜像名}/{版本}/{OS版本}/Dockerfile` 及其配套的 `README.md`），检查报 "Path Error"，导致 CI 失败。

PR 标题 `docs: ...` 表明这是一个纯文档更新，不涉及任何镜像的发布，但 CI 流水线中的 appstore 预检环节未区分"纯文档 PR"和"镜像发布 PR"。

## 修复方向

### 方向 1（置信度: 中）
**这是纯文档 PR，CI 判定属于误报。** 该 PR 不涉及任何应用镜像的构建或发布，根级 README 的 tags 信息更新属于正常的仓库维护工作，不应受 appstore 发布路径规范约束。建议：
- 确认该仓库的 CI 配置是否对根级 README 变更豁免 appstore 路径检查；若否，需向仓库维护者反馈此问题，由 CI 配置层面增加对纯文档 PR 的豁免逻辑。
- 若 CI 无法豁免，可将 tags 更新合并到下一次正式镜像发布 PR 中一同提交，避免单独文档 PR 触发此检查。

### 方向 2（置信度: 低）
CI 工具 `eulerpublisher` 的判断逻辑可能存在缺陷——将根级 `README.md` 的变更误判为需要参与 appstore 路径校验。但从日志、校验表格和 update.py:273 的报错语义来看，这更倾向于是 CI 流程设计上的限制（不区分文档 PR 与镜像 PR），而非工具本身的 bug。

## 需要进一步确认的点
1. 该仓库的 CI 流水线配置（Jenkinsfile 或等效文件）中，appstore 预检步骤是否对根级文件（如 `/README.md`、`/README.en.md`）有跳过/豁免逻辑。
2. 类似的纯文档 PR（历史上是否有人只改 README）此前是否成功通过该 CI 检查，以确认此问题是否为近期引入。
3. `eulerpublisher` 工具的 `update.py` 源码中路径校验逻辑的具体实现——"The expected path should be /README.md" 这一描述的含义需要对照源码确认：是期望文件在 `/README.md` 但 CI 未检测到，还是期望不存在根级 README 变更。
