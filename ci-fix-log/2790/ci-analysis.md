# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |

2026-06-29 15:21:41,552-[...]update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: `update.py`:222-273（appstore 发布规范预检阶段）
- 失败原因: CI 的 appstore 发布规范检查器（`update.py`）对所有 PR 变更文件执行 Docker 镜像目录路径结构校验，根目录级别的 `README.md` 和 `README.en.md` 不属于任何 Docker 镜像目录（不符合 `{Category}/{Image}/{Version}/` 路径模式），被校验器拒绝并报告 "Path Error"。PR 本身为纯文档更新（仅修改仓库根目录 README 文件），不涉及任何 Docker 镜像变更。

### 与 PR 变更的关联
PR 变更仅触及两个文件：`README.md` 和 `README.en.md`（均为仓库根目录文件，更新 openEuler 基础镜像可用标签列表）。这些变更触发了 CI 的 appstore 规范预检流水线，但该检查器未对"纯文档 PR"做豁免处理，导致两个文件均被判定为路径不符合 appstore 发布规范。**该失败与 PR 的代码内容无关，属于 CI 检查器覆盖范围过度的问题。**

## 修复方向

### 方向 1（置信度: 中）
CI 配置层面：为 appstore 规范预检步骤添加文件路径过滤器，排除仓库根目录文件（`README.md`、`README.en.md`、`CONTRIBUTING.md` 等）以及 `.claude/`、`.github/` 等非 Docker 镜像目录下文件的校验，使纯文档 PR 不再被误报。

### 方向 2（置信度: 低）
PR 内容层面：确认是否存在另一种可能性——即 `README.md` 中引用的某些 tag（如 `25.09`）对应的 Docker 镜像尚未在仓库中发布，检查器将其视为路径缺失。检查 `Base/openeuler/Dockerfile` 是否已支持 `25.09` 版本的基础镜像构建。

## 需要进一步确认的点
1. 查阅 `eulerpublisher/update/container/app/update.py` 第 222–273 行的具体路径校验逻辑，确认 "Path Error" 的触发条件和 "The expected path should be /README.md" 的实际含义。
2. 确认 CI 流水线是否有机制区分"仅文档变更 PR"与"含 Docker 镜像变更 PR"，若无则需在流水线中添加该判断分支。
3. 向 CI 团队确认 appstore 规范预检是否应当在非应用镜像 PR 上跳过——该预检设计初衷是校验 Docker 应用镜像目录结构完整性，不应在纯仓库 README 更新时执行。

## 修复验证要求
（不适用——本故障为 CI 基础设施问题，不涉及需要正则匹配上游源文件的修复场景。）
