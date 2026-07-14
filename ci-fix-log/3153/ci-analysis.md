# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: README路径格式校验
- 新模式症状关键词: Path Error, expected path, /README.md, appstore, README.md

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,839-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: PR 仅修改了 `README.md` 和 `README.en.md` 两个文档文件（添加新的基础镜像 tag 信息），但 CI 的 appstore 发布规范校验工具 `update.py` 将 diff 中检测到的 `README.md` 路径（`update.py:356`，不含前导 `/`）与内部期望的绝对路径 `/README.md` 进行比对，产生路径格式不匹配的误报。该失败并非由代码内容错误引起，而是 CI 校验工具对根级文档文件的路径规范化逻辑存在问题。

### 与 PR 变更的关联
PR 仅修改了两个 README 文档文件，更新了基础镜像可用 tag 列表（增加 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`，修正 `latest` 对应的 URL）。这些变更是纯文档更新，不涉及 Dockerfile、meta.yml 或任何镜像构建逻辑。CI 失败是因为 appstore 校验流程检测到根目录 `README.md` 被修改后触发了路径格式检查，该检查的内部比对逻辑有缺陷（git diff 产出的路径 `README.md` vs. 校验期望的 `/README.md`），属于 CI 工具层面的 bug，与 PR 代码质量无关。

## 修复方向

### 方向 1（置信度: 高）
CI 工具 `eulerpublisher/update/container/app/update.py` 中的 appstore 路径校验逻辑需对根级文档文件（如 `README.md`）做特殊处理，在路径比对前对 git diff 产出的相对路径统一添加前导 `/`，或跳过对非镜像构建相关文件的路径格式校验。

### 方向 2（置信度: 中）
该 PR 是纯文档变更 PR，CI 的 appstore 发布规范检查本不应被触发。修复方向是 `update.py` 在获取 diff 后跳过仅包含文档文件（以 `*.md` 结尾且不在镜像子目录下）的变更，或为 appstore 检查增加文件类型白名单过滤。

## 需要进一步确认的点
- `update.py:356` 处 diff 路径的生成逻辑（是直接用 git diff 的相对路径，还是经过了某种路径规范化处理）
- `update.py:273` 处的路径比对逻辑（期望路径 `/README.md` 的来源——是从仓库根路径拼接还是硬编码）
- 该 CI 校验步骤是否对纯文档 PR 有意设计为跳过检查，以及是否已有对应的文件过滤机制

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（无需填写——该修复不涉及外部源文件的正则匹配）
