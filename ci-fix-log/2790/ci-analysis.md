# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档路径校验格式不匹配
- 新模式症状关键词: Path Error, expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,677-update.py[line:222]-INFO: Clone https://gitcode.com/sunshuang1866/****-docker-images.git successfully.
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 修改了根目录 `README.md`，在校验路径格式时，工具内部预期路径为 `/README.md`（带前导 `/`），与 git diff 输出的 `README.md`（不带前导 `/`）做字符串比较时不匹配，判定为 Path Error。

### 与 PR 变更的关联
PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md` 两个纯文档文件，更新了基础镜像的 Supported Tags 列表。该 PR 不涉及任何 Dockerfile、构建逻辑或镜像制品的变更。CI 失败由 appstore 发布规范预检工具(eulerpublisher)的路径校验逻辑触发——该工具将根目录 README.md 的路径格式差异（有无前导 `/`）视为错误，而非 PR 的内容有实质性问题。

## 修复方向

### 方向 1（置信度: 低）
CI 工具 `update.py` 中的路径比较逻辑需要增加路径规范化处理（如统一去除前导 `/` 再做比较），以容忍 git diff 路径与内部规范路径在格式上的差异。此修复需要修改 CI 编排工具 `eulerpublisher` 本身的代码，而非本 PR 的 Dockerfile。

### 方向 2（置信度: 低）
如果 CI 工具的设计意图是阻止对根目录 `README.md` 的修改进入 appstore 发布流程（因为根 README 不属于任何镜像），则需要确认 PR 是否应该推送到正确的目标分支，或者 appstore 检查是否应该跳过纯文档类 PR。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py:273` 的完整路径校验逻辑，确认是字符串比较问题还是设计意图
- 根目录 `README.md` 是否在 CI 预期的可变更文件白名单中
- 同类纯文档 PR（仅修改根 README）历史上是否也会触发此检查
- 该 CI job 是否为必过项（blocking），还是可忽略的 warning 级检查
