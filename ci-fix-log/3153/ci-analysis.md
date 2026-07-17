# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（YAML / 元数据文件错误）

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范校验工具）
- 失败原因: CI appstore 发布规范检查器对 PR diff 中变更的唯一文件 `README.md` 执行路径格式校验，工具的路径比较逻辑判定 diff 路径 `README.md`（或 `a/README.md`）与预期绝对路径 `/README.md` 不匹配（缺少前导 `/` 或带有 git diff 前缀），导致校验失败。

### 与 PR 变更的关联
PR 仅修改根目录下的两个文档文件——`README.md` 和 `README.en.md`，更新了 openEuler 基础镜像的可用 tags 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目并修正对应链接）。改动本身不涉及任何 appstore 镜像提交（无 Dockerfile、meta.yml、image-info.yml 等），但 CI appstore 规范预检对所有变更文件一视同仁地执行路径格式校验，文档文件未豁免，导致报错。

## 修复方向

### 方向 1（置信度: 中）
这是 CI 校验工具对纯文档 PR 的误报。`update.py` 中 appstore 路径校验逻辑未区分"appstore 镜像提交"与"纯文档/仓库维护类变更"，对仅修改根级 README 的场景强制要求绝对路径 `/README.md` 格式，但 git diff 输出的路径（`a/README.md` 或 `README.md`）与该格式不匹配。修复应定位在 CI 工具层而非 PR 代码变更：在路径校验前规范化 diff 路径（统一添加前导 `/`），或为纯文档 PR 添加豁免路径。

### 方向 2（置信度: 低）
PR 的 README.md 修改内容中，新增 tag 条目的链接路径（如 `https://repo.openeuler.org/openEuler-24.03-LTS-SP4/docker_img/`）可能在 CI 解析后被判定为无效路径。需要逐一核实这些 URL 在 openEuler 镜像站上是否真实可访问。

## 需要进一步确认的点
1. `update.py:273` 及其附近路径比较逻辑的具体实现（如何从 diff 提取路径、预期路径格式定义、字符串匹配方式）
2. 历史成功合入的纯文档 PR 是否同样通过该 CI 检查——用于判断这是工具回归还是已有行为
3. CI 日志中显示运行由 **PR #3184**（分支 `fix/3153`）触发，而上下文标记 PR 为 #3153——需确认 PR #3184 是否引入了额外变更影响 CI 结果
4. 新增 tags 链接路径（`24.03-lts-sp4`、`25.09` 等目录）在 openEuler 镜像站是否均存在且可访问

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用——本失败不涉及 patch 外部源文件。
