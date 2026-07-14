# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: （无，匹配已有模式）
- 新模式症状关键词: （无）

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-.../update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 校验工具）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）将仓库根目录的 `README.md` 作为 appstore 发布候选文件进行路径校验，而 `README.md` 是仓库级别的文档文件，不属于任何应用镜像的 appstore 发布实体，无法满足 appstore 路径规范要求，导致校验失败。

### 与 PR 变更的关联
**此次 PR 变更与 CI 失败无直接因果关系。** PR 仅修改了 `README.md` 和 `README.en.md` 两个根目录文档文件（更新可用基础镜像 tags 列表），所有变更内容均为有效的文档更新。CI 失败的根本原因是校验工具将非 appstore 文件错误地纳入了 appstore 校验范围——即工具的文件过滤逻辑存在缺陷，任何仅修改仓库根级文档的 PR 都会触发相同的误报。

## 修复方向

### 方向 1（置信度: 中）
CI 校验工具 `update.py` 应在进行 appstore 路径校验前增加文件过滤逻辑，排除仓库根目录级别的非 appstore 文件（如 `README.md`、`README.en.md`、`LICENSE` 等），仅对位于应用镜像场景目录（`Bigdata/`、`AI/`、`Database/` 等）下的文件执行 appstore 发布规范校验。

### 方向 2（置信度: 低）
若无法修改 CI 校验工具，可在 CI workflow 配置层面对触发条件进行限制，使 appstore 预检 job 仅在 PR 涉及应用镜像目录内文件变更时触发，而非对所有 PR 一律执行。

## 需要进一步确认的点
- 需要查阅 `eulerpublisher/update/container/app/update.py` 源码（特别是第 273 行附近的校验逻辑和第 356 行的 diff 收集逻辑），确认文件过滤规则以及 `README.md` 被纳入校验范围的具体原因。
- 需要确认该 CI job（`multiarch/openeuler/x86-64/openeuler-docker-images` 下的 appstore 预检）是否预期对所有 PR 运行，还是仅针对包含应用镜像目录变动的 PR 运行。
- 需要确认 `[Path Error] The expected path should be /README.md` 中 `/README.md` 的具体含义：是期望路径格式为绝对路径（以 `/` 开头），还是期望文件位于某个 appstore 子目录路径之下。该细节对修复方向的选择有直接影响。
