# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档变更触发路径检查
- 新模式症状关键词: Path Error, expected path, README.md, README.en.md, appstore, specification errors, update.py

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
```

```
2026-07-12 15:33:08,211-update.py[line:356]-INFO: Difference: [
    "README.en.md",
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md` 文档文件（更新基础镜像可用 tags 列表），但 CI 的 appstore 发布规范校验器（`update.py`）被触发运行，它对所有变更文件执行路径合规性检查，根级文档文件不在任何镜像目录（如 `{category}/{image}/{version}/{os-version}/Dockerfile`）下，也不符合 appstore 发布规范的文件路径预期，因此被标记为 "Path Error"。

### 与 PR 变更的关联
PR 的改动（更新 README 中过时的基础镜像 tags 和链接）与失败**有直接关联但不是代码问题**：PR 仅修改了根级文档文件，没有任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 的变更。CI 流水线的 appstore 校验器被触发后，将这两个文档文件的 diff 纳入了检查范围，但该校验器预期检查对象是应用镜像发布目录下的结构化文件（Dockerfile、meta.yml 等），对根级文档文件产生了误报。**这不是 PR 代码本身的问题，而是 CI 校验流程对纯文档 PR 处理不当的配置/设计缺陷。**

## 修复方向

### 方向 1（置信度: 低）
关闭此 PR，通过其他不受 appstore 校验器约束的方式更新 README 文档（如由仓库管理员直接提交，或通过绕过该 CI 检查的流程）。但此方向意味着现有 CI 流程不支持通过普通 PR 更新根级 README 文件。

### 方向 2（置信度: 中）
CI 校验器 `update.py` 应在检测到变更文件仅涉及根级文档（`README.md`、`README.en.md` 等）且不包含任何镜像发布文件时，自动跳过 appstore 发布规范检查并直接放行。这需要修改 `eulerpublisher/update/container/app/update.py` 中的文件分类逻辑，将根级文档文件排除在路径校验范围之外。

## 需要进一步确认的点
1. `update.py` 中 `line:273` 附近的路径校验逻辑具体如何判断文件是否合规，以及是否有白名单/跳过规则可配置。需要查阅 `eulerpublisher/update/container/app/update.py` 源码以确认是否已有文档文件豁免逻辑但未生效。
2. 历史是否有纯文档 PR（仅修改 README 等根级文件）成功通过 CI 的案例，以判断这是一个新引入的问题还是一直存在的 CI 限制。
3. 确认 CI 流水线的触发配置：是否可能通过添加特定的 commit message 标签或 PR label 来跳过 appstore 校验步骤。
