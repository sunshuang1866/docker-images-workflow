# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 编排工具）
- 失败原因: CI 的 appstore 发布规范预检工具对 PR 中修改的仓库根层级 `README.md` 执行了路径校验，判定 `README.md` 不满足 `/README.md` 的预期路径格式。由于该文件本来就位于 `/README.md`，报错信息与实际文件路径存在矛盾，推测为 CI 工具对根层级文档文件的路径比较逻辑存在缺陷（如缺少或未正确添加路径前缀 `/` 进行归一化后比较）。

### 与 PR 变更的关联
PR 仅修改了仓库根目录下的两个 README 文件（`README.md` 和 `README.en.md`），更新了 openEuler 基础镜像的可用 Tags 列表（从 `24.03-lts-sp2` 改为 `24.03-lts-sp4`，并新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2`）。修改内容为纯文档变更，不涉及任何 Dockerfile、构建脚本或镜像元数据的改动。

此次 CI 失败**与 PR 代码变更的实际内容无关**，而是 CI 的 appstore 发布规范预检错误地将根层级 `README.md` 纳入了校验范围，或校验工具本身的路径归一化逻辑存在 bug。

## 修复方向

### 方向 1（置信度: 低）
CI 基础设施问题，**Code Fixer 无需修改 PR 代码**。需要 CI 平台维护人员排查 `eulerpublisher/update/container/app/update.py` 中 appstore 发布规范预检的路径比较逻辑：为何仓库根层级 `README.md`（路径即为 `/README.md`）会被报 `[Path Error]`。

### 方向 2（置信度: 低）
如果 CI 工具的设计意图是禁止非镜像目录下的文件被 PR 修改（该仓库中，合法的应用镜像文件位于 `AI/`、`Bigdata/` 等子目录下，根层级 `README.md` 不属于任何镜像条目），则需确认仓库是否允许在独立 PR 中修改根层级文档文件。若不允许，此 PR 本质上不应通过 CI。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 附近路径校验的具体逻辑——它是如何比较文件路径的（是否归一化、是否区分相对/绝对路径）。
2. 根层级 `README.md` / `README.en.md` 是否应当被纳入 appstore 发布规范预检的范围。
3. 是否存在其他仅有文档变更的 PR 也曾触发同类 `[Path Error]`（访问 CI 历史记录确认是否为已知基础设施缺陷）。

## 修复验证要求
（不适用——本报告结论为 infra-error，不涉及对 PR 代码的修改。）
