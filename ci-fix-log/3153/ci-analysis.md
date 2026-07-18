# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级文件误触发检查
- 新模式症状关键词: `Path Error`, `expected path should be /`, `appstore`, `README.md`, `根目录`

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
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR diff 中仅有 `README.md` 变更（无应用镜像相关文件），但其路径解析将 git diff 中的路径 `README.md`（不带前导 `/`）与期望格式 `/README.md`（带前导 `/`）进行了对比较，判定为路径格式不匹配。该 PR 仅修改了仓库根目录下的文档文件（`README.md` 和 `README.en.md`），本身不应触发 appstore 镜像发布规范的检查流程。

### 与 PR 变更的关联
本次 PR 变更仅涉及仓库根目录 `README.md` 和 `README.en.md` 中基础镜像 Tags 列表的文档更新（新增 24.03-lts-sp4、24.03-lts-sp3、25.09 条目，修正 latest 指向），不涉及任何应用镜像的 Dockerfile、meta.yml、image-info.yml 等构建或元数据文件。CI appstore 预检工具将仓库根级文档文件纳入了检查范围并因路径格式差异报错，属于 CI 工具边界处理的缺陷，与 PR 代码变更内容无实质关联。

## 修复方向

### 方向 1（置信度: 中）
CI 工具（`eulerpublisher/update/container/app/update.py`）的 appstore 预检逻辑需对仓库根目录文件（如 `README.md`、`README.en.md` 等）做豁免处理——这类非应用镜像目录下的文件变更不应触发 appstore 发布规范检查。需在 `update.py` 的 diff 文件过滤阶段增加对根级路径的判断，排除不属于任何 `image-list.yml` 注册路径内的文件。

### 方向 2（置信度: 低）
若 CI 工具暂无法修改，可通过 PR 提交策略绕过：将 README 文档变更与任何合法应用镜像变更（如任意 Dockerfile 的空行或注释修改）合并提交，使 CI diff 中包含至少一个符合 appstore 规范的有效文件，从而避免 README.md 单独被预检拦截。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中文件过滤逻辑的具体实现——确认是故意检查根级文件还是意外纳入。
2. 同一 CI 工具在涉及其他根级文件（如 `.gitignore`、`LICENSE`、`NOTICE`）变更时是否也会触发同类错误。
3. 确认 `update.py:222` 行克隆的是 `sunshuang1866` 仓库的分支，其中 README.md 的实际路径格式与工具期望的差异是否存在非标准 git 配置因素。
