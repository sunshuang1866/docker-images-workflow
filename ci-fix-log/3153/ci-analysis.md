# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: （不适用）
- 新模式症状关键词: （不适用）

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 修改了根目录 `README.md`，对其进行路径格式校验时发现实际路径 `README.md` 与期望的路径 `/README.md`（带前导 `/`）不匹配，判定为路径错误而失败。与此同时，被修改的 `README.en.md` 也面临同样的问题，但日志中仅展示了 `README.md` 的失败项。

### 与 PR 变更的关联
PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md` 两个文档文件（更新基础镜像可用 Tag 列表），未涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml。但 CI 流水线的 appstore 发布规范预检步骤对所有被修改的文件一视同仁地执行路径格式校验，导致根目录纯文档变更也被拦截。

该失败模式的本质与此前 PR #2512 中 `.claude/README.md` 路径校验失败一致（见历史知识库模式11中的多条 `.claude/` 路径校验失败案例），均属于 CI appstore 预检工具路径校验规则未能合理豁免非镜像目录文件的场景。

## 修复方向

### 方向 1（置信度: 高）
CI appstore 预检工具（`eulerpublisher/update/container/app/update.py`）应对仓库根目录下的纯文档文件（如 `README.md`、`README.en.md`）做白名单豁免，不纳入路径格式校验范围。修复点位于 CI 编排脚本/工具而非本仓库代码中，无法通过修改 Dockerfile 或 PR 内容绕过。

（如修复需在本仓库侧完成，可考虑在 CI 忽略规则中排除 `README*.md` 等根目录文档文件。）

### 方向 2（置信度: 中）
CI 预检工具中对路径的前导 `/` 处理逻辑存在不一致——实际检测到的路径为 `README.md`（无 `/` 前缀）而期望为 `/README.md`（有 `/` 前缀）。可能需要在路径比较前做标准化处理（统一加上或去掉前导 `/`），使根目录文件的路径校验能够通过。

## 需要进一步确认的点
- 需确认 `update.py` 中路径校验逻辑的具体实现，特别是为什么 `README.md` 与 `/README.md` 被视为不同路径。查看 `eulerpublisher` 仓库中 `update/container/app/update.py` 第 222-273 行的相关代码即可定位。
- 需确认 `README.en.md` 是否也被该检查拦截（日志中仅列出了 README.md），两个文件应面临同样的校验失败。
- 需确认该 CI 检查是否仅对经 appstore 流水线触发的 PR 生效，以及 `fix/3153` 分支为何被路由到 appstore 检查流水线而非普通的文档变更流水线。

## 修复验证要求
（不适用——本次失败为 CI 工具路径校验逻辑问题，不涉及正则 patch 外部源文件。）
