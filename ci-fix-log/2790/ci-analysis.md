# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式 (参考 模式11)
- 新模式标题: 根README路径校验失败
- 新模式症状关键词: Path Error, expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/openeuler/x86-64/openeuler-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

日志摘要：
```
2026-07-14 15:27:59,455-update.py[line:356]-INFO: Difference: [
    "README.md"
]
```

CI 的 `eulerpublisher` 工具检测到 PR 中仅有 `README.md` 被修改，随后在 appstore 发布规范预检中判定该文件路径不符合预期要求，返回 `FAILURE`。

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`，未包含任何 Dockerfile/meta.yml/image-info.yml 等镜像发布相关文件。CI 的 appstore 发布规范预检 (`update.py`) 在文件变更检查阶段将 `README.md` 判定为路径不符合 appstore 发布规范，直接终止 Pipeline。

### 与 PR 变更的关联

**直接触发**。PR 的变更内容为：

1. 将 `latest` 标签对应的版本从 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`
2. 新增 `25.09` 标签条目
3. 补充 `24.03-lts-sp3` 和 `24.03-lts-sp2` 的独立条目

此为纯文档变更，不涉及任何镜像构建文件的增删改。CI 的 appstore 发布规范预检阶段会将 PR 中所有变更文件纳入路径校验，根目录的 `README.md` 因不在任何镜像目录树（如 `AI/...`、`Bigdata/...`）下而被拒绝。该 PR 本身不存在代码/构建错误。

## 修复方向

### 方向 1（置信度: 中）
PR 的意图是更新根目录 README 中的 Tags 列表。若 CI 规范要求所有 PR 必须关联镜像发布，则此 PR 可能需要被标记为"文档类免检"或在 CI 工作流中增加对纯文档 PR 的跳过逻辑。确认仓库的 CI 规范是否允许不包含镜像变更的纯 README 更新 PR。

### 方向 2（置信度: 低）
若 CI 的 `update.py` 逻辑允许根目录 `README.md` 变更但当前存在 Bug（如路径比较方式导致误报），则需检查 `update.py:273` 处的路径校验实现。但根据日志"Difference: [\"README.md\"]"和表格式输出，该工具的设计意图即为校验变更文件是否符合 appstore 镜像发布路径结构，更可能是设计行为而非 Bug。

## 需要进一步确认的点
1. 该仓库 CI 是否允许不包含 Dockerfile/meta.yml 等镜像文件的纯文档 PR（如仅修改根目录 README）？
2. `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现——期望路径 `/README.md` 与实际检测到的路径之间的比较规则是什么？
3. 是否有 CI 配置（如 trigger job 中的条件判断）可以在检测到纯文档 PR 时跳过 appstore 预检阶段？

## 修复验证要求
（无需填写——本次失败为 CI 基础设施/流程问题，不涉及正则 patch 外部源文件。）
