# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验
- 新模式症状关键词: Path Error, expected path, README.md, appstore specification, eulerpublisher, update.py

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,839-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `README.md`（仓库根目录），检测由 `eulerpublisher/update/container/app/update.py:273` 触发
- 失败原因: CI 的 appstore 发布规范检查工具对 git diff 中检测到的变更文件 `README.md` 应用了镜像路径格式校验，根级 README.md 不符合镜像子目录的路径规范（如 `{category}/{image}/{version}/{os-version}/README.md`），被判定为路径错误

### 与 PR 变更的关联
**直接关联**。PR #3153 修改了仓库根的 `README.md`（更新基础镜像可用 tags 列表：将 latest 标签从 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`，新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目）。CI 的 diff 检测发现该文件变更后，将其纳入 appstore 发布规范路径检查流程。根级 README.md 作为仓库整体文档，本身不属于任何镜像目录，因此无法通过针对镜像子目录设计的路径校验。

PR 同时修改了 `README.en.md`，但 CI 的 diff 检测结果 `Difference: ["README.md"]` 中未包含该文件（可能被 CI diff 过滤或单独处理），故未触发同类校验失败。

## 修复方向

### 方向 1（置信度: 中）
CI 检查工具（`update.py:273`）应在路径校验前增加文件过滤逻辑，排除仓库根级文件（如 `/README.md`、`/README.en.md`、`.gitignore` 等非镜像子目录文件），仅对 `{category}/` 下的镜像子目录文件执行 appstore 发布规范路径检查。

### 方向 2（置信度: 低）
CI 工具可能存在路径字符串格式化问题——git diff 产出的路径为 `README.md`（无前导 `/`），而工具内部预期格式为 `/README.md`（带 `/` 前缀），两者字符串不等导致校验失败。需查阅 `update.py` 中路径比较逻辑确认。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中第 273 行附近路径校验函数的具体实现——校验的是 filepath 格式还是目录层级深度
- 根级 `README.md` 的历史 PR 中是否也曾触发同类校验失败，还是近期 CI 工具升级后新增的检查规则
- CI diff 检测为何仅报告 `README.md` 而未报告 `README.en.md`（是否为文件扩展名过滤逻辑）
- `Finished: FAILURE` 与 PR 状态一致，日志证据充分，无需额外确认

## 修复验证要求
无需从上游仓库获取文件进行正则匹配验证。但 code-fixer 在修改 CI 过滤逻辑时，需确认以下回归场景：
- 排除根级文件后，正常镜像子目录（如 `AI/xxx/1.0/24.03-lts-sp4/README.md`）的路径校验仍正常通过
- `README.en.md` 等其他根级非代码文件是否也需要加入排除列表
- 排除逻辑是否应与现有 `Difference` 检测（`update.py:356`）的过滤规则保持一致
