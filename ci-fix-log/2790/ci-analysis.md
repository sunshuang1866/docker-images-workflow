# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 路径前导斜杠缺失
- 新模式症状关键词: Path Error, expected path should be, appstore, README.md, 前导斜杠

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具 (`update.py`) 在路径比对时，期望文件路径以 `/` 开头（即 `/README.md`），但 git diff 输出的路径为 `README.md`（无前导斜杠），导致字符串比对不通过，判定为路径错误。

### 与 PR 变更的关联
PR 仅修改了两个根目录下的 README 文件（`README.md` 和 `README.en.md`），更新了可用镜像 Tags 列表（新增 24.03-lts-sp3、25.09 等条目）。文件本身位于正确的根目录位置，内容无格式或语法问题。失败完全由 CI 路径校验工具的前导斜杠格式要求与 git diff 输出的相对路径格式不兼容导致，与 PR 的实际改动内容**无关**。

## 修复方向

### 方向 1（置信度: 中）
CI 路径校验逻辑（`update.py` 第 273 行附近）在比对待检查文件路径时，未统一路径格式。git diff 输出的文件路径为相对路径（如 `README.md`），而校验器期望的预期路径带有前导 `/`（如 `/README.md`）。应在路径比对的入口处对双方做归一化处理（如统一添加或去除前导 `/`）。

### 方向 2（置信度: 低）
若 CI 校验工具的路径预期值（`/README.md`）是从仓库根目录的 `image-list.yml` 或其他元数据配置中读取的，则可能是 `image-list.yml` 中该条目的路径格式与标准不一致。但鉴于 PR 未修改任何元数据文件，此可能性较低。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py:273` 附近路径比对的具体逻辑，核实是字符串字面比对还是使用了路径归一化函数。
- 确认同一 PR 中 `README.en.md` 为何未被报告为路径错误——是否该校验仅针对 `README.md`，还是 `README.en.md` 也被检出但因格式一致而通过。

## 修复验证要求
无需验证。该失败为 infra-error，属于 CI 路径校验工具的格式处理缺陷，与 PR 代码变更无关，Code Fixer 无需处理 PR 内的 Dockerfile 或文档文件。
