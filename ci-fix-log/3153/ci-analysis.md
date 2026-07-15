# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-...-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检工具）
- 失败原因: CI 预检工具比对变更文件路径时，`git diff` 产出的路径为 `README.md`（无前导 `/`），而 appstore 规范校验逻辑期望的路径格式为 `/README.md`（带前导 `/`），两者字符串不相等导致校验失败。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 这两个仓库根目录的文档文件，内容为更新可用基础镜像 Tag 列表。变更本身**不涉及任何代码、Dockerfile、元数据文件或构建配置**，不应当触发 build/test/lint 失败。

失败由 CI appstore 发布规范预检工具路径比较逻辑引起——该工具检测到 PR 中包含 `README.md` 的变更后，按照 appstore 上架规范对该文件进行路径校验，但其字符串比较方式未能正确处理 git 相对路径与绝对路径格式的差异，导致误报。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 中的路径比较逻辑需要做路径格式归一化处理：在比较变更文件路径与期望路径之前，统一对两端进行规范化（如去除或添加前导 `/`，或使用 `os.path.normpath` 等标准库方法），确保 `README.md` 与 `/README.md` 被视为同一路径。

此修复应提交给 CI 工具（eulerpublisher）仓库，而非当前 Docker 镜像仓库。

### 方向 2（置信度: 低）
不排除 CI 流水线中 git clone 后的工作目录设定导致路径解析异常的可能。若确实如此，需调整下游构建 job 的工作目录或路径拼接逻辑。

## 需要进一步确认的点
1. `eulerpublisher` 仓库中 `update/container/app/update.py` 第 273 行附近路径校验逻辑的具体实现，确认字符串比较是否缺少路径归一化步骤。
2. 该 appstore 规范预检步骤是否为新增功能，或近期是否对路径格式要求有过变更——若是新引入的检查，可能存在未覆盖 root-level 文件路径格式的边界情况。
3. 确认 CI 检查仅报告了 `README.md` 而忽略了同 PR 中同样被修改的 `README.en.md`，这是否为预期行为（即 appstore 规范仅关注 `README.md`）。
