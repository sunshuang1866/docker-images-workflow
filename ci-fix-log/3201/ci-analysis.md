# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-17 04:00:32,038-...-INFO: Difference: [
    "AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile",
    "AI/maca-sdk/3.7/24.03-lts-sp3/EUR.repo",
    "AI/maca-sdk/README.md",
    "AI/maca-sdk/meta.yml"
]
...
  File ".../format.py", line 156, in parse_image_prefix
    raise ValueError(
ValueError: Missing required image root directory for multi-scene processing.
Required action: Specify the image root directory in AI/image-list.yml.
File: AI/maca-sdk/README.md
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `AI/image-list.yml`（缺失条目，非本次 PR 修改的文件）
- 失败原因: PR 在 `AI/maca-sdk/` 目录下新增了一个完整的镜像（含 Dockerfile、EUR.repo、README.md、meta.yml），但未同步更新 `AI/image-list.yml`，导致 CI 预检工具 `format.py` 的 `parse_image_prefix` 函数无法为其 `README.md` 解析出镜像根目录（image root directory），抛出 ValueError。

### 与 PR 变更的关联
**直接相关**。PR 新增了 `AI/maca-sdk/` 下的所有文件，根据项目规范（README 中明确要求"每个场景目录下必须包含一个 `image-list.yml`"），新增镜像时必须同时在对应场景的 `image-list.yml` 中补充该镜像根目录的条目。本次 PR 未包含对 `AI/image-list.yml` 的修改，导致 CI 校验阶段失败。该失败发生在 Docker 镜像构建之前，属于前置检查。

## 修复方向

### 方向 1（置信度: 高）
在 `AI/image-list.yml` 中新增 `maca-sdk` 镜像的根目录条目，格式参照该文件中已有的其他镜像条目。具体需要确认 `maca-sdk` 在 yml 中的 key 命名并填写其根路径（如 `AI/maca-sdk/3.7/24.03-lts-sp3/` 或 `AI/maca-sdk/`，取决于该 CI 工具对最小目录单元的定义）。

## 需要进一步确认的点
1. 查看 `AI/image-list.yml` 中现有条目的格式，确认 key 命名规范和 root path 的写法（全路径 vs 相对路径、是否包含版本号层级）。
2. 确认 `maca-sdk` 在 `image-list.yml` 中的 key 命名应与仓库中其他镜像的命名风格保持一致。

## 修复验证要求
无。本次修复仅涉及在 `AI/image-list.yml` 中补充配置条目，不涉及正则在第三方源文件中的匹配。
