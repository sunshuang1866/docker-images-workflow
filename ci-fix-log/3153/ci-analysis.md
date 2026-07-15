# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-eulerpublisher/update/container/app/update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,839-eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 eulerpublisher appstore 发布规范预检工具对仓库根目录 `README.md` 进行路径校验时，检测到的路径格式（`README.md`，无前导 `/`）与期望值（`/README.md`）不匹配，导致检查失败。PR 仅修改了 README.md 和 README.en.md 两个文档文件，未涉及任何镜像构建逻辑或元数据，该路径校验失败属于 CI 工具自身的字符串比较误报。

### 与 PR 变更的关联
本次 PR 变更仅涉及 README.md / README.en.md 中"可用镜像的 Tags"列表的文档更新（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目，调整排序）。变更本身不包含任何导致构建或测试失败的问题。CI 在 appstore 发布规范预检阶段对 `README.md` 根路径的校验失败与 PR 文档内容无关，属于 CI 工具侧路径格式匹配偏差。

## 修复方向

### 方向 1（置信度: 中）
CI 工具的路径比较逻辑可能存在前导 `/` 的严格匹配问题。检查 eulerpublisher `update.py` 中路径校验的字符串比较方式，确认是否需要对检测到的文件路径统一添加前导 `/` 或 normalize 后再进行匹配。此修复需由 CI 工具维护方完成，PR 作者侧无需改动。

### 方向 2（置信度: 低）
若 CI 工具的路径校验逻辑本身是正确的（即 README.md 确实不应通过该检查），则需确认 appstore 发布规范对根目录 README.md 是否有特殊豁免规则，并在 CI 校验工具中补充相应的 white-list 机制。

## 需要进一步确认的点
- eulerpublisher `update.py` 第 273 行附近 path 校验的具体实现逻辑（区分是文件系统路径格式差异还是内容引用路径差异）
- 同类纯文档 PR 在历史上是否也曾触发相同的 `[Path Error] The expected path should be /README.md` 失败（以判断是否为已知 CI 工具缺陷）
- 是否需要对根目录 README.md 的变更添加 CI 检查豁免
