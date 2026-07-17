# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具（eulerpublisher）对仓库根目录的 `README.md` 执行路径校验时，报告路径不匹配（期望 `/README.md`，但检测到的变更文件路径与其内部字符串比对逻辑不吻合），导致 checker 判定 FAILURE。PR 的 diff 仅包含对 `README.md` 和 `README.en.md` 的文档性修改（更新基础镜像 Tags 列表），无任何 Dockerfile、构建脚本或镜像配置变更。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅做了纯文档更新（在 README.md 和 README.en.md 的"可用镜像 Tags"表格中新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目，并修正 `24.03-lts-sp2/latest` 的链接从 SP1 路径改为 SP3 路径）。这是合法的文档维护操作，不涉及任何会影响构建或镜像发布的实质性代码变更。CI 失败源于 eulerpublisher 工具的 appstore 发布规范预检脚本对仓库根级 README 文件的路径校验逻辑存在问题（可能对 git diff 输出的路径格式与内部期望格式进行了过于严格的字符串比对），与 PR 改动内容本身无关。

## 修复方向

### 方向 1（置信度: 中）
**CI 工具侧修复**：eulerpublisher 的 `update.py` 中 appstore 规范检查逻辑在比对文件路径时，可能因 git diff 输出的路径前缀（如 `a/README.md` vs 期望的 `/README.md`）或路径规范化差异导致误报。修复需要调整 path 比对逻辑，而非修改任何 PR 代码。PR 作者/提交者无需对 README 做任何改动。

### 方向 2（置信度: 低）
**CI 流水线配置问题**：如果该仓库的 CI 配置规定 README 类纯文档 PR 不应触发 appstore 发布规范预检，则需要在触发条件中添加过滤规则，使仅涉及根目录 README 文件的 PR 跳过此检查步骤。

## 需要进一步确认的点
- eulerpublisher `update.py:273` 处的路径校验逻辑具体如何比对接收到文件路径的——是通过 git diff 输出还是文件系统遍历？是否存在路径前缀（如 `a/`）被纳入比较导致误匹配。
- 该仓库 CI 配置中是否对"仅 README 变更"的 PR 有跳过 appstore 检查的豁免规则（若有，则当前规则未生效是 bug；若无，则需 CI 团队评估是否需要添加此豁免）。
- `README.en.md` 同样被修改但未出现在 check 失败列表中——是已通过检查，还是检查工具只检查了 git diff 中的第一个/最后一个文件，需确认检查范围是否完整。

## 修复验证要求
（本报告判定为 infra-error，PR 代码侧无需修复。若 CI 团队决定修复工具逻辑，验证方式取决于工具代码的实际位置，不在本报告范围内。）
