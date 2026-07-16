# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 编排工具的 appstore 发布规范预检阶段）
- 失败原因: CI 工具从 git diff 中提取变更文件路径时，根目录下文件以 `README.md`（无前导 `/`）的形式出现，而 appstore 路径校验规则期望的格式为 `/README.md`（带前导 `/`），字符串比对不匹配导致误报 `FAILURE`。该检查在实际 Docker 构建之前执行，PR 中无任何 Dockerfile 变更或镜像提交，纯属 CI 工具路径归一化缺陷。

### 与 PR 变更的关联
PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（更新 supported tags 列表），属于纯文档变更。PR 不涉及任何 Dockerfile、镜像构建文件或 appstore 上架材料。CI appstore 预检阶段对所有变更文件进行路径校验，根目录下的 README.md 因 CI 工具路径前缀不一致被误判为不合规，该失败与 PR 的文档修改内容无关，属于 CI 基础设施工具的缺陷。

## 修复方向

### 方向 1（置信度: 高）
CI 编排工具 `eulerpublisher/update/container/app/update.py` 在路径比对时未做前导 `/` 归一化处理。应在 `update.py` 中，对从 git diff 提取的文件路径统一添加前导 `/`（或对期望路径模板去除前导 `/`），确保根目录文件的路径比对结果一致。

### 方向 2（置信度: 中）
若 CI 设计意图是仅对 appstore 上架相关的文件（如 Dockerfile、image-info.yml、meta.yml 等）执行路径校验，则应在 `update.py` 中增加文件过滤逻辑，将仓库根目录的纯文档文件（README.md、README.en.md 等）排除在 appstore 路径校验范围之外，避免非镜像提交 PR 触发误报。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py:273` 附近路径校验逻辑的具体实现，确认是否为简单字符串比对导致前导 `/` 不匹配。
- 确认 `eulerpublisher` 仓库中该工具是否已有相关 issue 或修复。
- 由于日志来自 x86-64 job 且已展示完整错误栈，本次分析无需下游架构日志即可定位于 CI 工具缺陷。

