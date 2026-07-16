# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: 不涉及项目源码，错误发生在 CI 编排工具 `eulerpublisher/update/container/app/update.py:273`
- 失败原因: PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（纯文档更新），但 CI 的 appstore 发布规范校验器对所有变更文件执行路径校验，将根目录的 `README.md`（相对路径表示）与预期格式 `/README.md`（绝对路径表示）进行比对后判定不匹配，导致校验失败。

### 与 PR 变更的关联
PR 仅更新了 `README.md` 和 `README.en.md` 中"可用镜像 Tags"列表的内容（将 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目），未涉及任何应用镜像 Dockerfile、meta.yml 或 image-info.yml。该文档变更本身是合法且正确的，CI 失败是 appstore 校验工具对根级文档文件的路径格式校验过于严格导致的误报（false positive）。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher` 的路径校验逻辑可能要求文件路径以 `/` 开头（如 `/README.md`），而 `git diff` 产生的路径表示为相对路径（`README.md`）。若此 PR 确需通过 appstore 校验流水线，在 `eulerpublisher` 源码中找到路径比较逻辑（`update.py` 或 `format.py` 中解析变更文件路径的部分），将相对路径归一化为绝对路径后再与预期值比较。

### 方向 2（置信度: 低）
若该 CI 流水线仅应用于涉及应用镜像目录（如 `AI/`、`Bigdata/`、`Cloud/` 等子目录）变更的 PR，而此 PR 为纯文档更新，则应从流水线触发条件中排除仅变更根级文档文件的 PR，避免误报。此方向需确认 CI 流水线的触发规则配置（不在本报告范围内）。

## 需要进一步确认的点
1. CI 日志中仅捕获了 x86-64 单架构 runner 的日志输出，未提供 aarch64 或其他架构 runner 的日志。若该 CI 流水线包含多架构构建阶段，需获取下游架构构建 job 的日志以排除是否存在真正的构建失败。
2. 需确认 `eulerpublisher/update/container/app/update.py` 中路径校验的完整逻辑，确认 `README.md`（无前缀 `/`）与 `/README.md` 的比对是否为导致 FAILURE 的唯一原因。
3. 确认该 CI 的触发/编排层 job（日志中显示 `Started by upstream project "multiarch/openeuler/trigger/openeuler-docker-images"`）是否对所有 PR 均执行 appstore 规范检查，还是仅对包含应用镜像变更的 PR 执行。
4. `README.en.md` 同样被修改但未出现在 CI 的检查结果表中——需确认 CI 工具是否仅检查 `README.md`，或 `README.en.md` 的变更是否被忽略/静默通过，这对判断问题范围有帮助。
