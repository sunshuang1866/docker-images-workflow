# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI路径校验误报根文档
- 新模式症状关键词: Path Error, expected path, README.md, appstore, specification errors

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-/.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对 PR 中变更的根目录 `README.md` 进行了路径校验，工具报告的 `[Path Error]` 提示表明该检查流程将根文档路径纳入了 appstore 镜像发布规范路径的校验范围，而根目录文档不应受此规则约束。

### 与 PR 变更的关联
PR #3153 仅修改了两个根目录文档文件（`README.md` 和 `README.en.md`），更新了基础镜像的可用 tags 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09` 条目，调整了 latest 指向）。PR 本身不涉及任何 Dockerfile、meta.yml、image-list.yml 等镜像构建与发布文件。CI 的 diff 检测到 `README.md` 变更后，appstore 规范校验器对该文件执行了路径校验，因根目录路径不符合 appstore 镜像发布路径的预期模式而报错。该失败实质上是 CI 工具对变更文件范围的处理逻辑问题——纯文档 PR 不应触发镜像发布路径校验。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `update.py` 中对 diff 变更文件的路径校验逻辑未排除根目录文档文件（如 `README.md`、`README.en.md`）。应在 CI 侧的路径校验逻辑中增加白名单/排除规则，使得根目录文档文件不被纳入 appstore 发布规范路径的校验范围。

### 方向 2（置信度: 低）
`update.py:273` 处理路径规范校验时的预期路径构造逻辑有误，对根目录文件未能正确归一化为绝对路径 `/README.md` 从而误报。需要排查 `update.py` 中路径校验函数的路径归一化逻辑。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的完整路径校验逻辑——确认是对所有 diff 文件无差别校验，还是有文件类型/路径过滤机制。
2. CI 触发条件：当前配置下，根目录 README 变更是否会触发 x86-64 架构构建 job。确认该 job 的触发规则是否应排除纯文档变更（`.github/workflows` 或 Jenkins Pipeline 配置）。
3. `update.py` 中第 222 行 `Clone ... successfully` 和第 273 行的 ERROR 之间发生了哪些校验步骤（日志中被省略的代码逻辑），以确认是否有其他校验项被跳过。

## 修复验证要求
若修复方向涉及修改 CI 工具代码（如 `eulerpublisher` 的 `update.py`），code-fixer 必须先复现 CI 的校验流程——使用与 CI 相同的 `eulerpublisher` 工具版本，在相同上下文下运行路径校验，确认修复后根目录 `README.md` 不再触发路径错误。若修复涉及 CI Pipeline 配置（如 Jenkinsfile 变更以排除纯文档 PR），需在同类 PR 上验证该触发排除规则生效。
