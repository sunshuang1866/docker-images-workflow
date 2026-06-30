# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (N/A)
- 新模式症状关键词: (N/A)

## 根因分析

### 直接错误
```
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: eulerpublisher/update/container/app/update.py:273
- 失败原因: CI appstore 发布规范预检器（`update.py`）扫描 PR 变更文件后，发现仓库根目录下的 `README.md` 和 `README.en.md` 不在任何应用镜像的最小目录单元（如 `AI/`、`Bigdata/` 等）内。appstore 发布规范要求 PR 中变更的文件必须归属于某个镜像目录，根级文档文件被视为不符合规范的路径，校验不通过。

### 与 PR 变更的关联
**直接关联**。PR #2790 仅修改了根目录 `README.md` 和 `README.en.md`（更新支持的镜像 Tags 列表，修正错误 URL），这两个文件触发了 CI appstore 发布规范路径检查，导致失败。若 PR 不涉及这两个文件的变更，该检查不会失败。

## 修复方向

### 方向 1（置信度: 高）
根目录 `README.md` 和 `README.en.md` 属于仓库级别的文档文件，不属于任何应用镜像目录。此类纯文档维护变更不应通过 appstore 发布流水线验证。建议通过不触发 appstore 检查的路径提交（如直接在 master 分支修改并推送，跳过 PR 流程），或在 CI 脚本 `update.py` 中将根目录 README 文件加入白名单排除。

### 方向 2（置信度: 中）
如果 CI 流水线支持通过 PR 标题标记（如 `[skip ci]`）或标签跳过部分检查，可在 PR 中使用该机制绕过 appstore 路径校验。

## 需要进一步确认的点
- `update.py` 中 `_parse_image_info` / 路径校验逻辑是否已提供排除根目录文件的配置项
- 仓库是否有明确的"纯文档修改"提交流程规范（是否允许直接推送到 master 而不走 PR）
- 是否存在其他同样位于根目录但允许被 appstore 检查忽略的文件列表

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——此次失败不涉及 patch 外部源文件）
