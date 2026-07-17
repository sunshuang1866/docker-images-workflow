# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验误报
- 新模式症状关键词: Path Error, expected path should be, README.md, appstore

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范检查工具对仓库根目录的 `README.md` 执行路径校验时，将 git diff 输出的相对路径 `README.md`（无前导 `/`）与期望的绝对路径格式 `/README.md`（有前导 `/`）进行字符串比较，因格式不一致而判定失败。这是 CI 工具的路径格式化/比较逻辑缺陷，而非 PR 代码内容问题。

### 与 PR 变更的关联
**无关。** PR #3153 仅修改了仓库根目录的两个文件：
- `README.md` — 更新基础镜像可用 tags 列表（修正 sp2→sp4 标签和链接地址）
- `README.en.md` — 同上（英文版）

这些都是纯文档更新，不涉及任何 Dockerfile、meta.yml、image-info.yml 或 Docker 镜像构建逻辑。CI 失败是由 appstore 发布规范预检工具在遇到根目录 README 修改时产生的路径校验误报，与 PR 的文档内容变更无关。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 此为 CI 基础设施问题（infra-error），需要 CI 管理员修复 `eulerpublisher` 工具中 `update.py` 的路径比较逻辑，使其对 git diff 提取的路径做前导 `/` 归一化处理（或反之剥离 `/` 后再比较）。Code Fixer 无需对 PR 代码做任何修改。

### 方向 2（置信度: 低）
如果 CI 管线预期根目录 README 不应参与 appstore 发布规范检查（根本身就不是应用镜像的 README），则应在检查逻辑中过滤掉仓库根目录的 `README.md` / `README.en.md`，仅针对应用镜像子目录内的 README 执行校验。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中路径比较逻辑的具体实现：是字符串精确匹配还是路径归一化后比较
- 该 appstore 检查是否应当将仓库根目录的 `README.md` 排除在校验范围之外（因为根 README 是仓库主文档，不是应用镜像的元数据文件）
- 是否存在其他仅修改根目录文档的 PR 也触发了相同错误（确认是否为近期 CI 工具升级引入的新问题）
