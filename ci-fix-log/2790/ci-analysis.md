# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）在扫描 PR diff 后发现 `README.md` 有变更，对其执行规范检查时报 `[Path Error] The expected path should be /README.md`。`README.md` 确实位于仓库根目录（即 `/README.md`），因此该错误并非指文件物理路径不正确，更可能是指 README.md 中列出的镜像 tag 所对应的 Docker 镜像目录路径在仓库中不存在、或 tag 描述文本中的路径格式不符合预期规范。

### 与 PR 变更的关联

本次 PR 仅修改了两个文档文件（`README.md`、`README.en.md`），变更内容为更新可用镜像的 Tags 列表：

1. 将主标签行从 `[24.03-lts-sp2, 24.03, latest]` 改为 `[24.03-lts-sp3, 24.03, latest]`，URL 同步从 `openEuler-24.03-LTS-SP1` 更新为 `openEuler-24.03-LTS-SP3`
2. 新增 `25.09` tag 条目及其 URL
3. 新增独立的 `24.03-lts-sp3` tag 条目（与第1条的组合标签形成**重复**：`24.03-lts-sp3` 在列表中出现了两次）
4. 新增独立的 `24.03-lts-sp2` tag 条目

CI 失败由 `README.md` 的变更直接触发。由于 CI 日志未提供 `update.py:273` 处检查逻辑的详细实现，无法确定是该检查在比较路径时的内部逻辑问题，还是 README 内容中新增 tag（如 `25.09`）对应的镜像目录在仓库中缺失所致。`24.03-lts-sp3` 重复出现也可能是规范违规的原因之一。

## 修复方向

### 方向 1（置信度: 中）
移除 README.md 中重复的 `24.03-lts-sp3` 条目（该 tag 已在组合标签行 `[24.03-lts-sp3, 24.03, latest]` 中声明），仅保留组合标签形式。同时检查新增的 `25.09` tag 是否有对应的 Docker 镜像目录存在于仓库中，若不存在则移除该条目或补充对应的镜像构建文件。

### 方向 2（置信度: 低）
CI 的 `eulerpublisher` 工具本身的路径检查逻辑可能对 README.md 的路径解析有特殊要求（如必须位于某个子目录而非根目录），或检查逻辑存在 bug。此可能性较低，需查阅 `update.py` 源码确认。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py:273` 附近的具体检查逻辑是什么？它检查的是文件路径、URL 路径、还是 tag 与镜像目录的对应关系？
- 仓库中是否存在与 `25.09` tag 对应的 `Base/openeuler/...` 镜像构建目录？
- README.md 中 `24.03-lts-sp3` 出现两次是否违反了 appstore 发布规范？
- `README.en.md` 同样被修改但未出现在 CI diff 中，CI 是否仅检查 `README.md`（中文版）？
