# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Root README 触发 appstore 校验
- 新模式症状关键词: update.py, Path Error, README.md, appstore, specification errors

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 规范校验工具）
- 失败原因: CI 的 appstore 校验工具对 PR 中所有变更文件执行 appstore 路径规范检查，根目录 `README.md` 不属于任何 appstore 镜像目录结构，工具将其视为路径不符合预期，报 `[Path Error]` 导致构建失败。

### 与 PR 变更的关联
PR #2790 仅修改了根目录的 `README.md` 和 `README.en.md`（基础镜像 Tags 列表的文档更新），不涉及任何 Dockerfile、meta.yml、image-list.yml 或 appstore 镜像文件。CI 的 appstore 校验工具不应将根目录文档文件纳入 appstore 路径校验范围，此次失败为校验工具的误报。

## 修复方向

### 方向 1（置信度: 中）
此失败属于 CI 基础设施问题：`eulerpublisher/update/container/app/update.py` 中的 diff 分析逻辑未过滤根目录文档文件，导致 `README.md` 被错误地纳入 appstore 路径校验。需修改 CI 校验工具 `update.py`，使其在检测到变更文件只涉及根目录文档（README.md、README.en.md 等）时，跳过 appstore 规范校验步骤，而非报错退出。

### 方向 2（置信度: 低）
若方向 1 不可行（CI 工具不允许修改），可考虑在 PR 中追加一个合法的 appstore 镜像变更（如新增 `meta.yml` 或 `image-info.yml` 条目）来满足校验工具要求。但此方向为 workaround，不应作为首选方案。

## 需要进一步确认的点
1. 查看 `eulerpublisher/update/container/app/update.py:273` 附近的 diff 遍历逻辑，确认其对根目录文件是否有过滤机制。
2. 确认其他类似纯文档 PR（仅修改根目录 README）是否也有相同失败，以排除环境特异性。
3. 确认该 CI job 的配置中 `update.py` 的调用方式是否支持跳过参数。

## 修复验证要求
由于本失败为 CI 工具层面的误报，非代码修复涉及正则 patch 外部源文件，无需额外验证。
