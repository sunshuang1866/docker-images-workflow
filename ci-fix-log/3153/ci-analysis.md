# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 根级文档路径校验
- 新模式症状关键词: Path Error, expected path, README.md, appstore

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-...-INFO: Difference: [
    "README.md"
]
...
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 修改了仓库根目录下的 `README.md`，但该文件不在 appstore 镜像发布规范的允许路径范围内。该 CI 检查预期所有变更文件应位于镜像子目录（如 `Bigdata/`、`AI/`、`Others/` 等）下的合法镜像发布路径中，仓库根级的纯文档文件（`README.md`）被当作不符合规范的路径而报告 `Path Error`。

### 与 PR 变更的关联
PR 仅修改了两个根级 README 文档文件（`README.en.md` 和 `README.md`），更新了可用基础镜像的 tags 列表。CI 预检工具在 `git diff` 中检测到 `README.md` 的变更后，将其纳入 appstore 发布规范校验范围，但因根级 `README.md` 不属于任何镜像发布目录而校验失败。这是 PR 变更**直接触发**的，但并非代码/构建逻辑错误——是 CI 校验规则不涵盖纯文档修改的边界情况。

## 修复方向

### 方向 1（置信度: 高）
CI appstore 预检工具在检测到非镜像发布路径的文件变更（如根级 README）时直接报错退出。应在 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑中增加白名单（如根级 `README.md`、`README.en.md`），使得纯文档修改的 PR 不被 appstore 发布规范校验阻塞。或者，调整 CI 流水线配置，使 appstore 预检仅对包含镜像目录变更的 PR 触发。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中路径校验的具体逻辑——确认当前是否对任何 `git diff` 检测到的文件都进行路径校验，还是已有部分白名单机制但遗漏了根级 README。
- CI 流水线配置（Jenkins job / trigger）中 appstore 预检 step 的触发条件——确认是否可以在不修改 `update.py` 的情况下，通过流水线配置跳过纯文档 PR。

## 修复验证要求
修复方向中包含对 CI 工具 `eulerpublisher` 源码的逻辑修改。code-fixer 必须：
- 先拉取 `eulerpublisher` 仓库源码，定位 `update.py:273` 附近的路径校验逻辑，确认当前校验实现细节。
- 修改后需在本地模拟 PR diff（仅含根级 README 变更），验证修改后的校验逻辑不再对根级文档报 `Path Error`。
- 同时验证仍能正确拦截真正不合规的镜像目录变更（如路径层级错误、缺少必要元数据文件等）。
