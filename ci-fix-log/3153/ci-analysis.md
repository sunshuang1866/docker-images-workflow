# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（部分匹配——appstore 发布规范校验失败）
- 新模式标题: —（非新模式，参见模式11）
- 新模式症状关键词: —

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-...[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检校验逻辑）
- 失败原因: CI 的 `eulerpublisher` 工具对变更文件 `README.md` 执行 appstore 发布规范校验时，判定其路径不符合要求——工具期望路径为 `/README.md`（带前导斜杠），但实际比较时路径为 `README.md`（不带前导斜杠），路径字符串不完全匹配导致校验失败。

### 与 PR 变更的关联
**与 PR 变更无实质关联。** PR 仅修改了项目根的 `README.md` 和 `README.en.md` 的文档内容（更新基础镜像可用 Tags 列表和对应的镜像站链接），属于纯文档修正，不涉及任何 Dockerfile、镜像构建、appstore 发布条目。CI 的 appstore 发布规范检查工具 `eulerpublisher` 将此纯文档 PR 中的根级 README 变更错误地纳入 appstore 路径校验范围，导致误报：根级 README 不属于任何镜像目录下的 README，不应受 appstore 路径约束，且文件实际就位于仓库根目录，路径本身没有问题。

## 修复方向

### 方向 1（置信度: 中）
**CI 工具路径比较逻辑存在前导斜杠不一致问题。** `eulerpublisher/update/container/app/update.py:273` 中输出变更文件路径 `README.md`（git diff 格式，不带前导 `/`）与过检时的预期路径 `/README.md`（带前导 `/`）未做路径归一化处理。对 `update.py` 中的路径比较逻辑做 `os.path.normpath` 或字符串级别的路径归一化（统一去除或添加前导 `/`）后再比较。

### 方向 2（置信度: 低）
**CI 工具未区分根级文档与镜像目录内文档。** CI 的 appstore 发布规范预检逻辑未过滤掉非镜像目录内的文件变更（如项目根级 README），将根级纯文档变更与镜像发布文件一同纳入校验。在 `update.py` 中增加变更文件的路由判断：若变更文件所在目录不在任何 `image-list.yml` 声明的镜像路径下，则跳过 appstore 路径规范校验。

## 需要进一步确认的点
1. 日志中所提及的 PR 编号为 #3184（分支 `fix/3153`），与本次分析的目标 PR #3153 编号不一致。需确认 CI 日志是否确实对应 PR #3153，以及 #3184 是否为 #3153 的后续衍生产生的新 PR。
2. `eulerpublisher/update/container/app/update.py:273` 处的具体路径比较逻辑需在代码库中确认——是否存在路径归一化缺失或镜像目录过滤缺失的 bug。
3. 需确认项目中根级 `README.md` 是否被 `image-list.yml` 的某条镜像路径覆盖（如被误注册为某个镜像的 README），若如此，移除该误注册即可解决。

## 修复验证要求
（本次失败的修复方向为 CI 工具逻辑调整，不涉及正则 patch 外部源文件，故无需从上游仓库拉取文件做正则验证。）
