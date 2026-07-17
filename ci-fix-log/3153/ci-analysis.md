# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 文档PR触发appstore路径校验
- 新模式症状关键词: Path Error, README.md, expected path, appstore, update.py, specification errors

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-.../update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（纯文档更新），不包含任何 Dockerfile、meta.yml 或 image-info.yml 等镜像发布所需文件。CI 的 appstore 发布规范检查器（`update.py`）对所有 PR 的变更文件执行路径校验，将根级 `README.md` 视作不符合镜像目录规范的异常文件，从而报 `[Path Error] The expected path should be /README.md` 并标记构建失败。

### 与 PR 变更的关联
PR 变更与失败无直接代码关联——此次 PR 的改动（更新基础镜像 tag 列表和对应下载链接）本身内容合法。失败由 CI 流水线逻辑问题触发：appstore 发布规范检查器未能识别纯文档 PR，误将其变更文件纳入镜像发布路径校验流程。

## 修复方向

### 方向 1（置信度: 中）
此失败为 CI 流水线的误报（false positive），与 PR 代码内容无关。PR 仅修改仓库根目录文档文件，不影响任何 Docker 镜像的构建和发布。建议 CI 流水线在 appstore 发布规范检查阶段增加文件变更类型判断：若变更仅涉及根级文档文件（`README.md`、`README.en.md` 等），应跳过 appstore 路径校验并直接放行，避免将纯文档 PR 误判为发布规范违规。

## 需要进一步确认的点
- 确认 CI 流水线 `update.py` 中 appstore 路径校验逻辑是否需要为纯文档 PR 添加跳过条件（检查位点：`update.py` 第 273 行附近的 `_check_*` 方法，以及第 356 行的 diff 计算逻辑）
- 确认类似的历史文档 PR 是否同样触发该误报，以判断此问题是偶发还是系统性缺陷
- 确认 PR #3184（日志中提及的 `sunshuang1866:fix/3153` 分支对应的实际触发 PR）与 PR #3153 的关系及差异范围
