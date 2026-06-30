# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-30 11:28:09,089-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具检测到 PR 变更了仓库根目录的 `README.md` 和 `README.en.md`，但这两个文件不属于任何 appstore 镜像目录，不符合 CI 工具预期的路径规范，导致预检失败。

### 与 PR 变更的关联
PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`，内容为更新支持的镜像 Tags 列表（新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，调整了 latest 标签关联）。CI 的 appstore 预检将这两个文件识别为"变更文件"后，对其执行了镜像发布路径合规校验——而仓库根目录的 README 文档不属于任何镜像目录，因此校验失败。失败由 PR 变更直接触发，但并非代码或构建错误。

## 修复方向

### 方向 1（置信度: 高）
该失败是 CI 预检工具对纯文档类 PR 的误判——仓库根目录的 `README.md` / `README.en.md` 不应参与 appstore 镜像发布规范检查。建议在 CI 流水线中为纯文档 PR 添加跳过 appstore 预检的逻辑，或在预检工具的 `update.py` 中排除非镜像目录下的 README 文件。

### 方向 2（置信度: 中）
如果 CI 流水线不支持跳过预检，可考虑将 README 更新单独提交到不受 appstore 预检约束的分支或仓库中，避免触发该检查。

## 需要进一步确认的点
- `update.py` 中 `_parse_image_info` 或类似的路径校验逻辑是否正确排除了仓库根目录文件
- 该 CI 预检步骤是否为所有 PR 的强制门禁，还是仅在特定触发条件下执行
- PR #2790 的变更意图是否为纯粹文档更新（是），是否可能被拆分为不触发 appstore 检查的提交方式
