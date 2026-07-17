# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

完整日志上下文：
```
2026-07-14 15:27:59,455 INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685 ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验工具（`update.py`）将本次 PR 视作镜像发布 PR 进行路径规范检查。`update.py` 发现 diff 中仅包含根层级 `README.md`，该文件不在任何镜像发布目录（如 `{category}/{image}/{version}/{os-version}/`）下，不符合 appstore 镜像发布所需的路径格式，因此判定为 `[Path Error]` 并标记为 `FAILURE`。

### 与 PR 变更的关联
本次 PR 仅修改了根层级 `README.md` 和 `README.en.md` 两个文档文件（更新"可用镜像的 Tags"列表：新增 24.03-lts-sp3、25.09、24.03-lts-sp2 等标签条目）。这些变更不涉及任何镜像 Dockerfile 的添加或修改，属于纯文档维护。

CI 流水线对所有 PR 统一执行 `eulerpublisher` 的 appstore 发布规范校验，该工具未识别出本次 PR 为纯文档 PR，仍以镜像发布标准进行路径校验，导致校验失败。属于 CI 校验工具对文档 PR 的误报，与 PR 代码变更的逻辑正确性无关。

## 修复方向

### 方向 1（置信度: 高）
本次失败为 CI appstore 校验工具对纯文档 PR 的误报。若需通过 CI，需要让 CI 流水线/触发器跳过对仅包含根层级 README 文件变更的 PR 的 appstore 发布校验。或者，将 README 更新与至少一个有效的镜像发布变更（如新增/修改 Dockerfile 等）合并提交，使 CI 校验有实体镜像路径可验证。

### 方向 2（置信度: 低）
从历史案例 PR #2512 模式11 看，同类 `[Path Error]` 的修复方式是调整文件位置使其符合 CI 期望的路径规范。但本次场景不同——`README.md` 本身就是仓库根层级文档，不应移至镜像子目录。此方向不适用于本次 PR 的实际情况。

## 需要进一步确认的点
- 确认 CI 触发器（`multiarch/openeuler/trigger/openeuler-docker-images`）是否有机制过滤仅含根层级 `README.md` 变更的 PR，跳过 appstore 发布校验。
- 确认仓库是否允许纯文档 PR 绕过 appstore 校验直接合入（如有相应 CI 策略）。
