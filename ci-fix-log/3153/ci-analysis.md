# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 模式11（部分匹配）
- 新模式标题: CI 路径校验误报
- 新模式症状关键词: Path Error, appstore, README.md, update.py, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 eulerpublisher 工具在执行 appstore 发布规范预检时，对仓库根目录的 `README.md` 报出 `[Path Error] The expected path should be /README.md`。但 `README.md` 确实位于仓库根目录，实际路径与期望路径 `/README.md` 一致。该错误为 CI 工具路径校验逻辑的误报，与 PR 的文档变更内容无关。

### 与 PR 变更的关联
PR #3153 仅修改了两个文档文件：
- `README.md`: 更新了基础镜像可用 Tags 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09 等 tag，更新 latest 指向）
- `README.en.md`: 与上述相同的内容变更（英文版）

PR 变更**不涉及**任何 Dockerfile、构建脚本、依赖配置或应用镜像目录结构。CI 失败完全由 eulerpublisher 工具的路径校验逻辑触发，与 PR 代码变更无实质关联。

## 修复方向

### 方向 1（置信度: 低）
CI 工具 `eulerpublisher/update.py` 中检查 appstore 发布规范的路径校验逻辑在处理仓库根目录文件（如 `README.md`）时存在缺陷，将本应通过的路径报为错误。需排查 `update.py` 中路径比较/归一化的实现——例如是否将不带前导 `/` 的相对路径与带 `/` 的绝对路径做字符串比较导致误判。

### 方向 2（置信度: 低）
该仓库对 `README.md` 的发布规范校验可能需要 PR 同时包含对应的 `image-list.yml` 或 `meta.yml` 变更（即 PR 仅修改文档不被视为合法的 appstore 发布提交）。若为设计意图，则 `[Path Error]` 错误信息未能清晰表达校验意图，属于 CI 工具错误信息的改进问题。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行附近 appstore 路径校验逻辑的具体实现——路径比较方式、预期路径模式
2. 同类仅修改 `README.md` 的文档 PR 是否也会触发相同失败（如无历史案例，建议用最小复现 PR 验证）
3. 仓库的 appstore 发布规范是否要求 README 变更必须伴随应用镜像提交（即纯文档 PR 是否被 CI 规则禁止）
4. `update.py:356` 处 diff 检测只报告了 `README.md` 而未报告 `README.en.md`，需确认这是设计行为还是工具缺陷
