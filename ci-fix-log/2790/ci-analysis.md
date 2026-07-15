# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径误报
- 新模式症状关键词: Path Error, expected path, README.md, appstore specification, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI appstore 发布规范检查工具在扫描 PR 变更文件时，对仓库根目录的 `README.md` 报出路径错误 `The expected path should be /README.md`。但 `README.md` 的实际路径正是 `/README.md`（仓库根目录），错误信息与事实矛盾，**判断为 CI 检查工具的误报（false positive）**。该检查工具可能仅设计用于验证应用镜像子目录下的文件路径规范，对根目录 `README.md` 的变更未正确处理。

### 与 PR 变更的关联
PR 仅修改了两个文档文件：
- `README.md` — 更新「可用镜像的 Tags」列表，新增 24.03-lts-sp3、25.09 等条目
- `README.en.md` — 同上（英文版）

CI appstore 检查工具因检测到 `README.md` 变更而触发路径校验，但校验逻辑对根目录文件存在误判，导致失败。**PR 本身的改动（文档内容更新）与 CI 失败无因果关系**。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 检查工具 `update.py` 的路径校验逻辑存在缺陷，对仓库根目录下的文件（如 `README.md`）给出了错误的路径判断。需要检查 `update.py` 中的路径规范校验函数（约第 270-280 行附近），排查为何 `/README.md` 的正规路径会被判定为不符合预期。可能的原因是校验规则仅覆盖了应用镜像子目录路径模式（如 `{category}/{image}/{version}/{os}/Dockerfile`），对根目录文件缺少豁免或正确匹配。

### 方向 2（置信度: 低）
若 CI 检查工具的路径校验依赖于特定的 repo 克隆方式或工作目录，克隆自 fork 仓库（`sunshuang1866/****-docker-images.git`）后临时目录路径拼接可能有差异，导致路径比对失败。

## 需要进一步确认的点
1. 确认 `eulerpublisher/update/container/app/update.py` 中路径校验的具体实现逻辑（约第 270-280 行），了解其对根目录文件的处理规则
2. 确认该 appstore 预检是否应当在纯文档 PR（无应用镜像变更）时被触发，或是否存在跳过检查的机制
3. 查看同类仅修改根目录 README 文件的历史 PR 是否也触发过类似失败

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不涉及。此失败为 CI 工具误报，修复方向为调整 CI 检查工具自身的路径校验逻辑。
