# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（部分匹配）
- 新模式标题: (不适用 — 已有模式部分匹配)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py` 第 273 行（appstore 发布规范预检工具）
- 失败原因: CI 的 appstore 发布规范预检工具检测到 `README.md` 被修改后，对其执行路径校验，期望路径应为 `/README.md`。但该检查可能对仓库根目录的 `README.md`（主仓库说明文档）和应用镜像的最小目录单元内的 `README.md`（镜像说明文档）采用了相同的校验规则，导致根目录 `README.md` 被误判为路径错误。此外，检查工具内部路径表示可能存在规范化不一致（如缺少/多余前导 `/`）。

### 与 PR 变更的关联
**与 PR 变更无直接因果关联**。本次 PR 仅修改了两个文件的文档内容，未引入任何新文件、未修改 Dockerfile：
- `README.md`：更新基础镜像标签列表，将 `24.03-lts-sp2` 替换为 `24.03-lts-sp4` 作为 `latest`，新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 标签条目及对应 URL
- `README.en.md`：同上（英文版）

`README.md` 文件路径未改变，始终在仓库根目录。CI 校验工具在检测到此文件变更后执行路径校验时产生了误报。

## 修复方向

### 方向 1（置信度: 中）
**CI 工具侧修复（非 PR 作者可控）**：CI 预检工具 `eulerpublisher` 的路径校验逻辑需要区分"仓库根目录的 README.md"和"镜像目录内的 README.md"，对根目录 README 豁免 `{category}/{image-name}/README.md` 格式的路径检查。此修改应在 `eulerpublisher/update/container/app/update.py` 中增加路径层级判断逻辑。

### 方向 2（置信度: 低）
**PR 侧规避（不推荐）**：如果在 CI 工具侧修复前需要快速绕过此检查，可考虑撤销对 `README.md` 的修改（仅保留 `README.en.md` 的更改），待工具修复后重新提交。但此举会导致中英文 README 内容不一致，不推荐。

## 需要进一步确认的点
1. 需要获取 `eulerpublisher/update/container/app/update.py` 第 273 行前后的路径校验源码，确认校验逻辑的具体实现，判断是对路径前导 `/` 缺失的误报，还是对根目录 README 的规则误用
2. 需确认仓库中是否有其他 PR 修改根目录 `README.md` 后通过该检查的历史案例，以判断是否为本次 CI 环境特有的瞬时故障
3. 如果可以，获取同级 `/job/aarch64/…` 的日志以确认是否存在架构相关的差异性失败（虽然目前证据指向前置预检阶段失败，与架构无关）

## 修复验证要求
无需特殊验证。此问题为 CI 基础设施工具的路径校验逻辑缺陷，与 PR 代码变更无关。若 CI 工具侧修复，验证方式为：提交仅修改根目录 README.md 的 PR，确认 appstore 发布规范预检通过。
