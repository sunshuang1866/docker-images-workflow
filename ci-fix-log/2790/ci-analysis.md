# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 纯文档PR误触发路径校验
- 新模式症状关键词: Path Error, README.md, appstore, expected path, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-.../eulerpublisher/update/container/app/update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py`（CI 编排工具的 appstore 路径校验阶段）
- 失败原因: CI 的 appstore 发布规范预检工具检测到变更文件为 `README.md`（根目录），该文件不符合 appstore 镜像发布所要求的路径规范（变更文件应在应用子目录如 `AppName/Version/Dockerfile` 等路径下），导致路径校验阶段直接失败。

### 与 PR 变更的关联
PR #2790 仅修改了两个根目录文档文件（`README.md` 和 `README.en.md`），内容是更新支持的镜像 Tags 列表（新增 24.03-lts-sp3、25.09 等版本条目）。这些变更本身语法和内容正确，属于纯文档类更新。但 CI 流水线在 PR 触发时自动执行了 appstore 发布规范预检，该预检期望 PR 变更文件为应用镜像相关文件（Dockerfile、meta.yml、image-info.yml 等），根目录 `README.md` 不符合其预期路径格式，导致校验失败。**此失败与 PR 的代码内容无关，变更本身没有问题。**

## 修复方向

### 方向 1（置信度: 高）
此 PR 为纯文档更新（README.md），不涉及任何应用镜像的增删改，可直接跳过 appstore 发布规范预检。联系 CI 管理员或在 CI 流水线配置中将 `README.md` / `README.en.md` 等根目录文档文件加入 appstore 路径校验的白名单/排除列表，使其在仅修改文档时不触发该检查。

### 方向 2（置信度: 中）
如果该仓库 CI 不支持跳过检查，则考虑通过 `[skip ci]` 或类似机制标记此 PR 为纯文档变更，让 CI 流水线在预检阶段识别并自动放行。

## 需要进一步确认的点
- CI 流水线（Jenkins）的 appstore 预检配置中是否存在文件路径白名单机制，如有则确认 `README.md`、`README.en.md` 是否应被列入排除项。
- 确认触发该 CI 检查的 upstream PR（日志中显示为 PR #3194，分支 `sunshuang1866:fix/2790 → master`）的触发策略，是否对所有 PR 均强制执行 appstore 路径校验。

## 修复验证要求
此问题无需修改 Dockerfile 或源代码文件，无需额外验证。若修改 CI 流水线配置，需在同类纯文档 PR 上验证修改后的白名单机制是否生效。
