# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-...update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（文档更新），但 CI 流水线启动了 appstore 发布规范校验（`eulerpublisher` 工具），该工具将根目录 `README.md` 作为待上架镜像的元数据文件进行路径合法性检查，判定其为不符合 appstore 规范的路径。

### 与 PR 变更的关联
本次 PR 仅修改了仓库根目录的两个 README 文件，更新了"可用镜像的 Tags"列表（新增 24.03-lts-sp3、25.09、24.03-lts-sp2 等版本的标签信息），不涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 等镜像构建文件。该失败与 PR 变更内容本身**无直接关联**——问题出在 CI 流水线对文档类 PR 进行了不必要的 appstore 路径校验。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线或 `eulerpublisher` 工具的 appstore 校验逻辑缺少对纯文档变更 PR 的过滤机制。应在校验前增加判断：当 PR 仅涉及仓库根目录的 README/README-en 等文档文件时，跳过 appstore 规范性检查，避免误报。

### 方向 2（置信度: 低）
根目录 `README.md` 的文件路径在 CI 工具中期望以 `/README.md`（带前导 `/`）格式出现，而 git diff 生成的路径为 `README.md`（无前导 `/`），路径格式不匹配导致校验失败。但这一可能性较低，因为 git diff 下根目录文件的标准路径形式即不加前导斜杠。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py:273` 附近及 `:356` 的完整逻辑，确认路径校验的白名单/黑名单机制。
- CI 流水线配置中是否有条件判断来决定是否执行 appstore 校验步骤（如仅当 PR 涉及镜像目录下的文件时才触发）。
- 仓库是否定义了用于标记"纯文档更新、跳过 appstore 检查"的标签或 CI 跳过机制。
