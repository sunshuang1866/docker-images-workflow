# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检（`update.py`）检测到 PR 变更了根目录下的 `README.en.md` 和 `README.md` 两个纯文档文件，将其与 appstore 镜像发布路径规范（期望 Docker 镜像相关目录结构）进行比对，判定两个文件均不符合规范，报告 `[Path Error]`。

### 与 PR 变更的关联
**直接关联**：本 PR 仅修改了 `README.en.md` 和 `README.md` 两个根目录文档文件（更新基础镜像可用 tags 列表），没有任何 Docker 镜像构建文件（Dockerfile、meta.yml 等）的变更。CI 的 appstore 发布规范预检期望 PR 包含符合 `{image-version}/{os-version}/Dockerfile` 结构的镜像提交，对纯文档变更未做豁免处理，导致两个文件均被标记为路径错误。

PR 变更内容（URL 更新）本身是正确的文档维护操作，不包含任何代码错误。

## 修复方向

### 方向 1（置信度: 高）
CI 的 appstore 发布规范预检应增加对纯文档变更 PR 的豁免逻辑。当 PR 仅修改根目录下的 `README.md`、`README.en.md` 等文档文件且不涉及任何镜像构建文件时，跳过 appstore 规范检查，允许通过。可在 `update.py` 的差异分析阶段（约第 356 行附近，`Difference:` 日志输出处）添加文件过滤，排除不在镜像目录下的文档文件。

### 方向 2（置信度: 中）
如果 CI 侧不便修改豁免逻辑，则本 PR 应在提交时附带一个合法的"占位"镜像变更条目（如对某个现有镜像的 `meta.yml` 做一次空操作修订），以满足 CI 预检对"必须有镜像变更"的要求。但此方案为 workaround，不推荐。

## 需要进一步确认的点
- `update.py` 中 appstore 路径校验的具体逻辑（`line:273` 附近的 check 函数），确认其是否有文件类型/路径前缀白名单机制。
- 同类纯文档 PR 在该仓库中历史上是否有通过 CI 的先例，以判断本次失败是否为 CI 规则近期收紧所致。

## 修复验证要求
无需验证（本失败不涉及正则 patch 外部源文件）。
