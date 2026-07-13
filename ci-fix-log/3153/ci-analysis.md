# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 文档变更触发CI拒绝
- 新模式症状关键词: Path Error, expected path, appstore, specification errors, README

## 根因分析

### 直接错误
```
2026-07-12 15:33:08,211-.../update.py[line:356]-INFO: Difference: [
    "README.en.md",
    "README.md"
]
...
2026-07-12 15:33:13,075-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: PR 仅包含 `README.md` 和 `README.en.md` 两个文档文件的变更，不包含任何 Dockerfile 或镜像元数据文件（如 `meta.yml`、`image-list.yml`）。CI 的 appstore 发布规范校验（`update.py`）要求 PR 中必须包含符合路径规范的 Docker 镜像文件，纯文档变更不满足该校验条件，被判定为 Path Error。

### 与 PR 变更的关联
PR 的变更（更新 README 中可用的基础镜像 tag 列表）直接触发了失败——但并非因为变更内容有误，而是因为变更类型本身（纯文档）不被 CI 的 appstore 发布校验所接受。该 CI 校验步骤对所有 PR 强制执行，检查变更文件是否符合 Docker 镜像发布规范（如 `{category}/{image}/{version}/{os-version}/Dockerfile` 路径格式），README 文件不在此规范内，因此被拒绝。

## 修复方向

### 方向 1（置信度: 中）
纯文档类 PR 不应触发 appstore 发布规范的路径校验。需要确认 CI 流水线中是否缺少对文档类 PR 的跳过逻辑——例如，检查变更文件是否全部为非 Dockerfile 的文档文件，若是则跳过 `update.py` 的 appstore 路径校验步骤。

### 方向 2（置信度: 低）
若该仓库要求所有 PR（包括文档）必须通过 appstore 校验，则需在 PR 中同时包含 Docker 镜像相关文件（如 `image-list.yml` 中注册 README 条目），使 README 变更成为镜像发布的一部分。

## 需要进一步确认的点
1. CI 流水线在 `update.py:273` 之前是否有文档类 PR 的跳过逻辑？若有，为何未生效？需查看 `update.py` 源码中 `Difference` 检测后的处理逻辑。
2. 同一仓库中过往的纯文档 PR（如有）是否也曾被此校验拦截？若未被拦截，需对比 PR diff 差异。
3. `README.en.md` 文件名是否需要调整为其他格式以满足 appstore 规范？
