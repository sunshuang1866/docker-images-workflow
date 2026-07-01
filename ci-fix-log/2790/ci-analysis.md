# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552 update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具 `update.py` 检测到 PR 变更文件 `README.en.md` 和 `README.md` 后，对这两个根目录文档文件执行了路径校验，校验结果显示二者均不符合 appstore 期望的路径格式（`/README.md`），导致预检失败。

### 与 PR 变更的关联
PR 仅修改了根目录下的 `README.md` 和 `README.en.md` 两个纯文档文件（更新支持的镜像 Tags 列表）。这些是仓库级别的说明文档，并非任何应用镜像的 Dockerfile 或元数据文件。CI 的 appstore 预检环节对所有 PR 变更文件均执行路径规范校验，但根目录文档文件本不应被纳入 appstore 镜像发布规范检查的范围——该检查的设计目标是校验 `{image-version}/{os-version}/Dockerfile` 等镜像目录结构的合规性。PR 的内容变更本身没有错误，CI 流水线在校验范围上存在误判。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 预检脚本 `update.py` 在校验文件路径时，未排除仓库根目录的文档文件（如 `README.md`、`README.en.md`）。修复思路是让 CI 脚本在扫描变更文件列表后，过滤掉明显不属于镜像目录结构的根级文档文件（可通过文件名白名单或路径深度判断），使纯文档类 PR 不再被 appstore 路径检查拦截。

### 方向 2（置信度: 低）
`README.en.md` 的文件名可能不符合 CI appstore 对英文 README 的命名或路径约定（如要求位于特定子目录下或统一命名为 `README.md` 配合语言标记）。但尚不明确 CI 是否对英文 README 有具体的存放规范要求。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现（特别是 `[Path Error] The expected path should be /README.md` 这条消息的触发条件），以确认为何 `README.md` 自身也会被判定为路径错误。
2. CI appstore 预检是否有"仅作用于镜像目录内文件"的预期范围界定，当前是否因配置不当导致根目录文档文件被误纳入校验。
3. 该仓库历史中，是否有其他仅修改根目录 `README.md` 的 PR 通过了 CI（用于判断这是否为新引入的 CI 配置回退）。
