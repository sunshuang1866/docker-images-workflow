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
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |

2026-07-12 15:33:13,075 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: CI 流水线中的 appstore 发布规范预检阶段（`eulerpublisher/update/container/app/update.py:273`）
- 失败原因: PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（纯文档变更），但 CI 的 appstore 发布规范检查器将这两个根级文件也纳入了路径校验。检查器期望这些文件的路径符合 appstore 镜像发布规范（如 `{image-version}/{os-version}/` 模式），而 `README.md` 和 `README.en.md` 作为仓库根级文档，不在 appstore 发布规范路径白名单内，导致校验失败。

### 与 PR 变更的关联

PR 仅更新了 `README.md`（中文）和 `README.en.md`（英文）中"可用镜像 Tags"表格的内容——新增了 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 四个 tag 条目，并将 `latest` 标签的链接从 SP1 更新为 SP4。变更是纯文档内容的增删，不涉及任何 Dockerfile、镜像元数据（`meta.yml`、`image-info.yml`）或 `image-list.yml` 的改动。

此次 PR 的变更**本身没有问题**。CI 失败是由于 CI 流水线对根级文档文件的校验过于严格——appstore 发布规范检查不应作用于仓库根目录的 README 文件。这与 PR #3153 的变更内容无关，属于 CI 基础设施层面的误报。

## 修复方向

### 方向 1（置信度: 高）

CI 的 appstore 发布规范预检步骤（`update.py` 中的路径校验逻辑）需要增加过滤条件：对于仓库根级文件（如 `README.md`、`README.en.md`、`CONTRIBUTING.md` 等），应跳过 appstore 路径规范检查。此类根级文档文件不属于任一镜像发布目录，不应被纳入 appstore 发布规范校验范围。

代码层面的调整点：在 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑中，对检测到的变更文件列表增加根级文件过滤（例如路径不以场景目录 `AI/`、`Bigdata/`、`Storage/`、`Database/`、`Cloud/`、`HPC/`、`Distroless/`、`Others/`、`Base/` 开头时跳过校验）。

### 方向 2（备选，置信度: 低）

若 CI 在设计上确实要求所有 PR 都必须通过 appstore 规范校验（包括纯文档 PR），则可考虑将 README 文件的变更也纳入 appstore 发布流程中，但这显然不合理且不符合项目惯例。

## 需要进一步确认的点

- `eulerpublisher/update/container/app/update.py:273` 的具体路径校验逻辑，确认其是否对根级文件有白名单或排除机制
- CI 流水线是否有针对"纯文档变更 PR"的快速通道或跳过某些检查的机制
- 其他仅修改根级 README 的 PR 是否也曾触发同类 CI 失败

## 修复验证要求

（本次失败为 CI 基础设施误报，不涉及正则 patch 外部源文件，因此无需填写此节。）
