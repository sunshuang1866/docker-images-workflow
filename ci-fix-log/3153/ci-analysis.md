# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI文档PR路径误检
- 新模式症状关键词: Path Error, expected path, README.md, appstore specification, update.py

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839- update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

CI 差异检测仅捕获 `README.md`：
```
2026-07-14 11:27:51,489- update.py[line:356]-INFO: Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范检查工具（`update.py`）对纯文档修改的 PR 执行了路径校验，将仓库根目录下的 `README.md` 误判为不符合 appstore 镜像路径规范，报 "The expected path should be /README.md"。PR 本身仅修改 README 文档内容，不涉及任何 Dockerfile 或应用镜像元数据文件，CI 工具不应对此 PR 执行 appstore 规范检查。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 中基础镜像可用标签的描述信息：
- 将 24.03-lts-sp2 → 24.03-lts-sp4（latest 标签指向）
- 新增 24.03-lts-sp3、25.09、24.03-lts-sp2 条目

这两个文件位于仓库根目录，不属于任何应用镜像的子目录结构。PR 中不包含任何 Dockerfile、meta.yml、image-info.yml、image-list.yml 等应用镜像发布相关文件的变更。CI 工具将文档变更错误地纳入 appstore 发布规范检查范围，导致误报。

值得注意的是，CI 差异检测（`update.py:356`）仅输出 `["README.md"]`，遗漏了同样被修改的 `README.en.md`，这可能暗示 CI 工具的变更文件检测逻辑本身存在缺陷。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施 / 流水线配置问题，与 PR 代码变更无关。需联系 CI 管理员：
1. 将仓库根级文档文件（`README.md`、`README.en.md`、`CONTRIBUTING.md` 等）加入 appstore 路径校验的白名单；
2. 或调整 CI 触发条件，使 appstore 规范检查仅在 PR 涉及应用镜像目录（即包含 Dockerfile/meta.yml/image-info.yml 的路径）时才执行，而非对所有 PR 一律执行。

### 方向 2（置信度: 低）
若 CI 差异检测仅输出 `README.md` 是 `update.py` 的缺陷（遗漏 `README.en.md`），则还需修复该工具的变更文件检测逻辑，确保能完整识别所有变更文件。但即使修复了检测逻辑，结果可能只是多一个 `README.en.md` 的相同误报，并不会改变根本问题。

## 需要进一步确认的点
1. 确认 `update.py:273` 路径校验逻辑：是对所有变更文件强制执行 appstore 路径规范检查，还是存在白名单机制而 `README.md` 未被纳入？
2. 确认 CI 差异检测仅输出 `README.md` 而遗漏 `README.en.md` 的原因——`update.py` 是如何计算 PR 变更文件列表的？
3. 确认该 CI job（`x86-64/openeuler-docker-images`）是否为架构专属；若 aarch64 等其他架构 job 也存在相同误检，需一并处理。
4. 确认此前是否有类似的纯文档 PR 通过同一 CI 检查成功——若之前可以而现在不行，则可能是 CI 工具版本更新引入了回归。

## 修复验证要求
无需修改 PR 代码内容。若 CI 配置调整后，建议通过一个类似的纯文档修改 PR 验证 appstore 规范检查不再对根级文档文件报错。
