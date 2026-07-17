# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-...-INFO: Difference: [ "README.md" ]
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: PR #2790 仅修改了根目录下的 `README.md` 和 `README.en.md`（项目级文档文件），CI 的 appstore 发布规范预检工具（`eulerpublisher`）要求所有被检文件必须符合 `{category}/{image-name}/{version}/{os-version}/` 的 appstore 镜像目录路径规范，根目录 README.md 不属于任何 appstore 应用镜像发布条目，因此路径校验失败。

### 与 PR 变更的关联
PR 的变更完全触发了此失败。该 PR 仅修改了 README 文件中的镜像版本标签列表（将 latest 从 24.03-lts-sp2 更新为 24.03-lts-sp3，并补充 25.09、24.03-lts-sp3、24.03-lts-sp2 标签链接），未涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 等 appstore 镜像相关文件。CI pipeline 的 appstore 发布规范预检阶段要求所有变更文件必须落入合法的 appstore 镜像目录路径，根目录文档文件不满足该约束。

## 修复方向

### 方向 1（置信度: 高）
该 PR 是纯文档修正，不应触发 appstore 发布规范预检。如果 README 更新确实需要通过此 CI pipeline 合入，需确认该 CI job 是否可以跳过对根目录非 appstore 文件的路径校验，或者通过 CI 配置将 `README.md` / `README.en.md` 加入白名单。

### 方向 2（置信度: 中）
如果此 CI pipeline 仅接受 appstore 镜像相关文件的变更，则此 PR 应通过其他 workflow（非 appstore release pipeline）提交和合入。

## 需要进一步确认的点
- CI pipeline 中 `multiarch/openeuler/trigger/openeuler-docker-images` 的触发条件：是否对所有 PR 都触发，还是仅对匹配特定文件路径模式的 PR 触发。如果所有 PR 都经过 appstore 发布规范预检，则纯文档变更 PR 需要考虑如何绕过该检查。
- 为何 CI 只检测到 `README.md` 的变更而未能看到 `README.en.md` 的变更（日志中 `Difference: ["README.md"]` 仅包含前者），需确认差异检测逻辑。

## 修复验证要求
（无需验证上游源文件，不适用。）
