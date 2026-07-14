# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: 文档PR误触发AppStore路径校验
- 新模式症状关键词: Path Error, expected path, appstore, README.md, documentation-only

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 流水线中的 AppStore 发布规范检查工具（`eulerpublisher`）检测到 PR 变更包含 `README.md`，对其执行了应用镜像上架路径校验，认定根目录下的 `README.md` 不符合 AppStore 镜像的路径规范（期望路径应为镜像特定的 `/{category}/{image-name}/README.md` 格式），从而判定失败。

### 与 PR 变更的关联

**与 PR 变更无关（误报）。** 该 PR 仅修改了仓库根目录的两个文档文件（`README.md` 和 `README.en.md`），更新了基础镜像可用 Tags 列表及其对应的下载链接。PR 中不包含任何 Dockerfile、`meta.yml`、`image-info.yml` 或 `image-list.yml` 等镜像构建/发布相关文件。CI 的 AppStore 规范检查不应针对纯文档类 PR 中根目录 README 变更触发路径校验，此失败为 CI 检查流程的误报。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线的 AppStore 检查步骤缺少对纯文档变更 PR 的豁免逻辑。应在 `eulerpublisher/update/container/app/update.py` 或 CI 触发条件中增加过滤：当 PR 的变更文件仅限于仓库根目录的 `README.md` / `README.en.md`（或更广义的文档类文件）且不涉及任何镜像构建目录时，跳过 AppStore 发布规范检查。

### 方向 2（置信度: 低）
本 PR 实际无需修复——问题出在 CI 侧。若 CI 侧短期内无法调整检查逻辑，可尝试重新触发 CI 运行（re-run），观察是否为 Jenkins runner 的瞬时异常（如 clone 的 fork 仓库状态与预期不一致导致的误判）。

## 需要进一步确认的点
1. CI 日志中 `Difference: ["README.md"]` 表明检查工具仅发现了 `README.md` 变更，但 PR diff 中实际修改了两个文件（`README.md` 和 `README.en.md`）。需确认 `README.en.md` 是否也被检查或是否已有豁免逻辑。
2. `eulerpublisher/update/container/app/update.py` 中第 222-273 行的完整检查逻辑（错误行号已知但完整源码未提供），确认是否有基于文件路径前缀（如 `AI/`、`Bigdata/` 等）的过滤机制。
3. 历史 PR #2512 的路径校验失败案例是否已有对应的 CI 豁免修复，若有则需确认该修复为何未覆盖本 PR 的场景。
4. 确认该 CI Job 是否为所有 PR 的必经检查（mandatory check），以及是否有维护者手动 bypass 的机制。
