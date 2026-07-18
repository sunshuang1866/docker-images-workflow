# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（YAML / 元数据文件错误 — CI appstore 路径校验失败）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685 update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范校验步骤）
- 失败原因: CI 的 appstore 发布规范校验工具对 `README.md` 进行路径检查时，将实际路径 `README.md` 与期望路径 `/README.md` 进行比较并判定不匹配，导致校验失败。`README.md` 位于仓库根目录，实际路径应当等同于 `/README.md`，校验工具可能因缺少路径前导斜杠的归一化处理而误报。

### 与 PR 变更的关联
PR #2790 仅修改了两个文件：`README.md` 和 `README.en.md`（更新支持的镜像 Tags 列表、新增 24.03-lts-sp3 / 25.09 等条目）。CI 的 diff 检测阶段识别到 `README.md` 变更后，触发了 appstore 发布规范校验流程，校验工具对该文件进行路径合规性检查并失败。此失败直接由此次 PR 的文件变更触发，但失败原因（路径格式校验）与 PR 的内容修改（文档内容更新）本身无关。

## 修复方向

### 方向 1（置信度: 中）
这是 CI 校验工具的路径比较方式问题。校验工具在比较文件路径时可能未对相对路径（如 `README.md`）添加前导 `/` 归一化处理，而期望路径使用绝对形式的 `/README.md`，导致字符串不匹配。修复方向为：检查 CI 校验脚本 `eulerpublisher/update/container/app/update.py` 中路径比较逻辑，确保在比较前对文件路径做归一化处理（统一添加前导 `/` 或统一去除前导 `/`）。

### 方向 2（置信度: 低）
也可能 `README.md` 在仓库克隆后实际位于不同于根目录的路径（如被 git clone 到子目录导致）。但日志显示差异检测正常识别文件名为 `README.md`，且后续校验也是针对同一路径，此可能性较低。

## 需要进一步确认的点
- CI 校验工具 `update.py` 中路径比较的具体实现逻辑（第 273 行附近的路径校验代码），确认路径归一化方式。
- 仓库被 CI 克隆后的实际目录结构，确认 `README.md` 是否确实位于克隆目录的根层级。
- 该 CI 校验是否对 root README 文件有特殊的豁免规则（因为项目根目录的 README.md 不属于应用镜像发布范畴，不应受 appstore 规范约束）。

## 修复验证要求
（不适用——本次失败未涉及正则 patch 外部源文件）
