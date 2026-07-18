# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式（部分关联 模式11）
- 新模式标题: 根目录文档被 Appstore 检查误拦
- 新模式症状关键词: README.md, Path Error, expected path, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-.../update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范检查工具检测到 PR 变更了 `README.md`（仓库根目录），并将该文件纳入 appstore 发布规范的路径校验。由于 `README.md` 位于仓库根目录而非任何 `Image_i/` 镜像目录内，不符合 appstore 镜像发布所要求的路径格式，校验判定 `FAILURE`。

### 与 PR 变更的关联
PR #2790 仅修改了仓库根目录的两个文档文件（`README.md` 和 `README.en.md`），更新了可用镜像 Tags 列表（新增 24.03-lts-sp3、25.09 等条目，调整顺序）。这些变更**不涉及任何 Dockerfile、meta.yml、image-info.yml 或镜像目录**，属于纯文档维护改动。

CI 的 appstore 发布预检将根目录 `README.md` 错误地作为待发布的应用镜像文件进行校验，导致本不应触发的检查失败。该失败**与 PR 变更内容无关**——即使 README 内容是合法的，根目录文档也不应在 appstore 镜像发布校验范围内。

## 修复方向

### 方向 1（置信度: 中）
CI 编排工具 `eulerpublisher` 中的 appstore 发布预检逻辑过于宽泛，将所有变更文件（包括仓库根目录的 README）都纳入了 appstore 路径校验。应当在预检中增加过滤条件，仅对位于 `image-list.yml` 所管理的镜像目录内的文件执行路径校验，跳过仓库根目录及纯文档目录下的文件。

### 方向 2（置信度: 低）
`update.py` 对根目录 `/README.md` 的路径解析逻辑存在问题——文件实际位于仓库根目录 `/README.md`，而校验器也期望路径为 `/README.md`，两者理应匹配却判定失败，不排除路径规范化（如末尾斜杠、相对/绝对路径比较）存在 bug。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py` 中 appstore 路径校验逻辑的完整过滤规则——根目录文件是否本应被排除。
- 确认 `update.py` 第 273 行前后的校验逻辑，判断错误是因为"文件不在预期路径"还是"路径字符串比较方式有缺陷"（如 `/README.md` vs `./README.md` vs `README.md`）。
- 该 PR #2790 的 CI 失败 label 是否必要——纯文档变更 PR 不应被 appstore 检查阻塞。
