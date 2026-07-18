# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（变体）
- 新模式标题: CI路径归一化缺陷
- 新模式症状关键词: Path Error, expected path should be, /README.md, appstore

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI appstore 发布规范预检工具（`eulerpublisher`）对根目录下的 `README.md` 进行路径校验时，将文件路径 `README.md` 与期望路径 `/README.md` 进行字符串比较，因缺少前导 `/` 导致匹配失败。`README.md` 实际位于仓库根目录，路径本身正确，问题出在 CI 工具的路径归一化逻辑中（未对根目录文件路径统一添加前导 `/`）。

### 与 PR 变更的关联
本 PR 仅修改了 `README.md` 和 `README.en.md` 两个根目录下的文档文件，更新了可用镜像 Tag 列表（新增 25.09、24.03-lts-sp3、24.03-lts-sp2 条目，并修正了 24.03-lts 的链接从 SP1 更新为 SP3）。CI 失败并非由 PR 的文档内容变更引起，而是 CI 工具在对变更文件进行路径格式校验时触发了自身的路径归一化缺陷——该缺陷对任何修改根目录文件（如 `README.md`）的 PR 均可能触发。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题，与 PR 代码变更无关。应在 `eulerpublisher` 工具（`update/container/app/update.py`）的路径校验逻辑中修复路径归一化：对变更文件路径统一添加前导 `/` 后再与预期路径进行比对，或确保比对双方使用一致的路径格式（均带或不带前导 `/`）。

### 方向 2（置信度: 低）
若 CI 工具的路径校验逻辑确实有明确的 schema/映射表定义每个允许文件的期望路径，则可能是该映射表中缺少对 `README.md`（根目录）的正确条目配置，需补齐。

## 需要进一步确认的点
1. 确认 `eulerpublisher` 工具的路径校验逻辑源码（`update.py` 中 `line:273` 附近的校验函数），验证是否为路径归一化缺陷。
2. 确认该 CI 失败是否仅在当前 PR 出现，还是其他修改根目录 `README.md` 的 PR 也出现同样错误——若为普遍现象，则确认为 CI 工具 bug。
3. 确认 `README.en.md` 为什么没有出现在 CI 的 `Difference` 列表中（日志显示只有 `README.md`），是否存在 CI 工具对变更文件检测不完整的问题。
