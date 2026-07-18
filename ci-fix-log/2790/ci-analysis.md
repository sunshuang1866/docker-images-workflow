# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验失败
- 新模式症状关键词: Path Error, expected path should be, appstore, update.py, README.md

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:356]-INFO: Difference: [ "README.md" ]
2026-07-14 15:28:07,677-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:222]-INFO: Clone https://gitcode.com/sunshuang1866/****-docker-images.git successfully.
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 修改了仓库根目录的 `README.md`，但其路径校验规则要求文件路径为 `/README.md`（绝对形式），或该工具对根目录文件的变更未做兼容处理（工具设计上预期 PR 仅包含应用镜像子目录下的文件变更），导致校验失败。

### 与 PR 变更的关联
PR #2790 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`，内容为更新支持的镜像 Tags 列表（将 latest tag 从 24.03-lts-sp2/SP1 修正为 24.03-lts-sp3/SP3，并补充 25.09、24.03-lts-sp3、24.03-lts-sp2 条目）。这些是合法的文档更新，但触发了 CI appstore 发布规范预检工具对根目录文件变更的路径校验拦截。失败与 PR 变更直接相关，但错误不在 PR 内容本身——属于 CI 校验工具对根 README 变更场景的处理缺陷。

## 修复方向

### 方向 1（置信度: 中）
CI 校验工具 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑不兼容仓库根目录文件的变更。该工具预期 PR 变更文件位于应用镜像子目录（如 `Bigdata/`、`AI/` 等）内，对根目录 `README.md` 做路径格式检查时未正确处理相对路径与绝对路径的归一化，或直接将其归入无效路径。修复应在 CI 层：使 `update.py` 的路径检查对仓库根目录文件（`/README.md`、`/README.en.md`）做白名单豁免，而非拒绝。

### 方向 2（置信度: 低）
若 CI 校验工具的路径检查机制无法在短期内调整，可考虑将 README 变更拆分为独立 PR 或通过其他渠道提交（如直接推送到 master），避开 CI appstore 预检。但此方向仅是变通方案，不解决根因。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 及其调用的路径校验函数的具体实现逻辑，确认是否为绝对路径 vs 相对路径的正则匹配问题。
2. `Difference: [ "README.md" ]` 中为何只检测到 `README.md` 而未列 `README.en.md`——是 diff 处理逻辑只取第一个文件，还是有意过滤了 `.en.md` 文件。
3. CI appstore 预检的路径规则文档，确认仓库根目录文件是否在预期范围内。
