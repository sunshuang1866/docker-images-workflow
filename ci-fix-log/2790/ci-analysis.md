# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: README触发appstore路径校验
- 新模式症状关键词: Path Error, expected path, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

CI 差异检测日志：
```
update.py[line:356]-INFO: Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范校验工具）
- 失败原因: PR 只修改了根目录下的 `README.md` 和 `README.en.md`（纯文档变更），但 CI 流水线的 appstore 发布规范预检阶段（`update.py`）将 `README.md` 纳入校验范围，并报告 `[Path Error] The expected path should be /README.md`。文件在仓库中的实际路径就是 `/README.md`，错误信息本身自相矛盾（期望路径与实际路径一致却判定 FAILURE），说明 CI 校验工具对该文件的路径检查逻辑存在异常，或根级 README.md 不在 appstore 发布规范所预期的文件范围内，被误纳入校验流程。

### 与 PR 变更的关联
- **PR 变更内容**: 仅修改 `README.md` 和 `README.en.md`（新增 25.09、24.03-lts-sp3/latest、24.03-lts-sp2 三个 tag 条目；修正 latest tag 关联链接从 SP1 到 SP3）。未改动任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml。
- **触发关系**: PR 的文档变更被 CI 流水线的 appstore 发布规范预检步骤捕获，`update.py` 识别出变更文件 `README.md` 后执行路径校验并报错。该失败并非由 PR 文档内容错误引起，而是 CI 校验工具将不应参与 appstore 校验的根级 README 纳入检查范围所致。

## 修复方向

### 方向 1（置信度: 中）
CI 校验工具 `eulerpublisher/update/container/app/update.py` 在 appstore 发布规范预检中，可能错误地将根级 README.md 纳入路径校验范围。根级 README.md 属于项目级文档而非应用镜像相关文件，appstore 校验应只检查 `image-list.yml` 中注册的镜像目录内的文件。需确认 `update.py` 是否存在路径白名单或过滤逻辑缺失，导致根级文档被误检。

### 方向 2（置信度: 低）
若 CI 校验工具行为是预期设计（即所有 PR 变更文件均需通过 appstore 路径校验），那么 README.md 的 diff 路径格式（相对路径 `README.md` 无前导 `/`）可能与校验工具的内部规范格式（绝对路径 `/README.md` 带前导 `/`）存在匹配不一致，导致字符串比较失败。但这种情况下校验结果的"期望路径"应显示与实际路径不同的值，而非当前显示的相同值。

## 需要进一步确认的点

1. **CI 校验工具源码审查**：需查阅 `eulerpublisher/update/container/app/update.py` 第 273 行附近的路径校验逻辑，确认其对根级 README.md 的处理规则（是否应该跳过、是否有白名单）。
2. **同类 PR 对比**：确认其他仅修改 README.md 的 PR 是否也会触发同样的 Path Error，以判断该失败是普遍现象还是本 PR 的特例。
3. **PR 合并权限**：确认 README-only 变更的 PR 是否应该触发 appstore release pipeline，或者应配置为跳过该 pipeline 阶段。

## 修复验证要求
无。此次失败不涉及 Dockerfile 构建或第三方文件 patch，验证要求仅适用于修改正则以匹配上游源文件的场景。
