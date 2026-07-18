# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (无——匹配已有模式)
- 新模式症状关键词: (无)

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
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）在扫描 PR 变更文件时，检测到仓库根目录的 `README.md` 被修改，对其执行路径校验后发现不满足 appstore 期望路径 `/README.md`（工具内部路径比较可能存在格式差异，如有无前导斜杠、或期望文件位于镜像子目录而非仓库根目录）。

### 与 PR 变更的关联
**间接关联**。PR 本身仅修改了 `README.md` 和 `README.en.md` 中的基础镜像 tag 列表和对应 URL（纯文档更新），并非引入新 Docker 镜像。但 CI 的 appstore 发布规范预检流程会将所有 PR 变更文件纳入检查范围，导致仓库根目录的 `README.md` 被误判为不符合 appstore 镜像发布路径规范。若 PR 不触及根 `README.md`（如仅新增或修改某个应用镜像子目录下的文件），则不会触发此检查失败。

## 修复方向

### 方向 1（置信度: 中）
CI 预检工具的路径校验逻辑对仓库根目录文件（非 Docker 镜像目录下的文件）过于严格。根目录 `README.md` 是仓库文档文件，不属于任何应用镜像的 appstore 发布条目，不应被纳入 appstore 路径规范检查。需要在 CI 预检工具（`eulerpublisher/update/container/app/update.py`）中增加过滤逻辑：跳过仓库根目录非镜像文件（如 `README.md`、`README.en.md`、`.github/` 等）的路径校验。

### 方向 2（置信度: 低）
`update.py` 中路径比较使用了不一致的前导斜杠格式（如实际路径为 `README.md`，工具比较时拼接了 `"/" + filename` 产生 `/README.md`）。修复路径归一化逻辑即可通过校验。但此方向与"仓库根 README 本不应参与 appstore 校验"的业务语义相悖，优先推荐方向 1。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行附近 appstore 规范检查的具体逻辑（路径归一化方式、文件过滤条件）。
2. 确认仓库中是否确实有约定：根目录 `README.md` 不应参与 appstore 发布规范检查（需查看 CI 配置或 `eulerpublisher` 工具源码中的文件排除规则）。

## 修复验证要求
若修复涉及 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑，code-fixer 必须在本地模拟 PR #3153 的场景（仅修改根目录 `README.md`），重新运行 CI 预检脚本以验证修复后不再报 `[Path Error]`。同时需确保正常镜像目录下的 `README.md`（如 `AI/xxx/README.md`）仍能通过正常的路径校验。
