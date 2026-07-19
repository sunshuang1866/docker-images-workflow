# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具代码，非 PR 文件）
- 失败原因: CI appstore 发布规范预检工具在解析 PR diff 时，将 `README.md`（git diff 路径格式，无前导 `/`）与预期路径 `/README.md`（仓库根路径格式）进行严格字符串比较，因缺少前导 `/` 而导致路径校验失败。PR 仅修改了 README.md 和 README.en.md 中的文档内容（更新基础镜像 tag 列表和对应下载链接），未修改任何文件路径或目录结构。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #3153 是纯文档修改，变更内容为：
- 将 `24.03-lts-sp2` 的 latest 标签改为 `24.03-lts-sp4`
- 新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 四行 tag 条目
- 修正各条目的下载链接指向对应的 openEuler 版本目录

失败是 CI 工具 (`eulerpublisher`) 的路径校验逻辑问题：`update.py` 中 `git diff --name-only` 输出的文件路径格式（`README.md`，无前导 `/`）与 appstore 规范定义的期望路径格式（`/README.md`，带前导 `/`）不匹配。该问题在任何涉及根级 `README.md` 变更的 PR 上均会触发。

## 修复方向

### 方向 1（置信度: 低）
**CI 工具路径比较逻辑容错**：在 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑中，对 git diff 输出的路径添加前导 `/`（或对预期路径去除前导 `/`）后再进行字符串比较，使两种路径表示形式一致。此修复应在 CI 工具仓库中完成，而非在本 PR 的 openEuler 镜像仓库中。

### 方向 2（置信度: 低）
**CI appstore 预检白名单**：将仓库根级的 `README.md` 和 `README.en.md` 加入 appstore 发布规范预检的白名单，因为这些文件是仓库级文档而非应用镜像级文件，无需满足 appstore 的路径规范。此修复同样应在 CI 工具仓库中完成。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中第 273 行前后的路径校验逻辑具体实现，确认路径比较方式
- CI 工具 `eulerpublisher` 是否有独立仓库和版本号，需要在 CI 工具侧提交修复
- 该 appstore 路径预检功能是否为新上线的检查项（该检查之前是否对 README.md 也能正常通过）
- 日志中显示的 `PR 3184 [sunshuang1866:fix/3153 -> master]` 与上下文 PR #3153 的关系：日志来自 PR #3184（针对 #3153 的修复分支），两 PR 可能属于同一修复链路，需确认实际触发 CI 的 PR

## 修复验证要求
（不适用——本失败为 infra-error，无需修改 PR 代码，需在 CI 工具侧修复路径比较逻辑。）
