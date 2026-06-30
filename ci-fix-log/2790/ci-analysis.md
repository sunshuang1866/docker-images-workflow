# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11（变体）
- 新模式标题: （不适用，已有模式匹配）

## 根因分析

### 直接错误
```
2026-06-30 11:28:09,089-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检脚本检测到 PR 中变更的文件为根目录下的 `README.md` 和 `README.en.md`，这两个文件不属于任何应用镜像目录结构（不符合 `{category}/{image-name}/{version}/` 等 appstore 发布规范），被判定为路径不合规。

### 与 PR 变更的关联
PR 仅修改了两个根级文件 `README.md` 和 `README.en.md`（新增 24.03-lts-sp3、25.09 等镜像 tag 的文档链接），无任何 Dockerfile 或应用镜像相关文件的变更。CI 的 appstore 发布检查工具直接对这些变更文件执行路径校验，因根级 markdown 文件不属于任何合法的应用镜像发布路径而失败。**该失败由本次 PR 变更直接触发**。

## 修复方向

### 方向 1（置信度: 高）
此 CI job 是 x86-64 架构的应用镜像发布流水线，其 appstore 规范检查假定 PR 变更内容必定与应用镜像发布相关。纯文档类 PR（仅修改根级 README）不需要经过此流水线验证。如需合入此 PR，应与 CI 管理员确认是否需要旁路该 job，或确认纯文档 PR 是否应在触发层（trigger job）即被跳过下游架构构建 job。

### 方向 2（置信度: 中）
若该 CI 流水线的设计意图是"任何 PR 都必须经过检查"，则 CI 脚本中的路径校验逻辑缺少对根级 README 文件的白名单豁免。需要在 `update.py` 中增加对 `README.md`、`README.en.md` 等根级文档文件的跳过/豁免逻辑。

## 需要进一步确认的点
- 该 CI job（`openeuler-docker-images` x86-64）是否设计为只处理包含 Dockerfile 变更的应用镜像 PR。如果是，则纯文档 PR 不应触发此 job。
- 上游 trigger job（`multiarch/openeuler/trigger/openeuler-docker-images`）是否应对纯文档 PR 进行过滤并跳过下游架构构建。
- aarch64 等其它架构的对应 job 是否也产生了相同错误（日志中仅包含 x86-64 job 的输出）。
