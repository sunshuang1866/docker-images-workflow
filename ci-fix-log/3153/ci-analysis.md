# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11

## 根因分析

### 直接错误

```
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范检查工具将根目录下的 `README.md` 纳入路径校验范围，但该文件为纯文档文件，不属于应用镜像发布制品，不满足 appstore 路径规范

### 与 PR 变更的关联

**该失败与本次 PR 的代码变更内容无关。** PR 仅修改了 `README.md` 和 `README.en.md` 两个文件，更新了 openEuler 基础镜像的可用标签列表和对应链接（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 四个标签条目）。这是一次纯粹的文档更新，不涉及任何 Dockerfile、meta.yml、image-info.yml 或应用镜像构建逻辑。

CI 失败是因为 appstore 规范预检工具 `update.py` 对 **所有** PR diff 中的文件执行路径校验，根目录级别的 `README.md` 被误判为不符合 appstore 发布路径规范，导致预检失败。

## 修复方向

### 方向 1（置信度: 高）
**CI 流水线侧处理**：在 appstore 预检工具（`update.py`）中，将根目录 `/README.md` 和 `/README.en.md` 加入路径白名单或排除列表，使其不被纳入 appstore 发布规范的路径校验范围。这属于 CI 工具配置问题，而非 PR 内容问题。

### 方向 2（置信度: 中）
**CI 触发条件优化**：修改 CI 触发逻辑，当 PR 仅包含根目录文档文件的变更（无 Dockerfile、meta.yml、image-info.yml 等应用镜像相关文件）时，跳过 appstore 发布规范预检步骤。

## 需要进一步确认的点

1. `eulerpublisher/update/container/app/update.py` 的具体路径校验逻辑——确认 `[Path Error] The expected path should be /README.md` 的具体含义：是路径缺少 `/` 前缀的格式问题，还是根目录 README 不在 appstore 预期路径白名单中
2. 该 CI 预检步骤是否有历史 PR 成功通过（相同类型的 README-only 变更），以确认是否为本次 CI 环境特有的问题
3. 若 PR 包含 README.md 变更但同时也有应用镜像文件变更（如 Dockerfile），该预检是否会通过——以区分"路径格式错误"与"文件类型不在范围内"两种根因

## 修复验证要求

无。本次失败为 infra-error（CI 工具校验逻辑问题），与 PR 代码变更无关，Code Fixer 无需对 PR 文件做任何修改。
