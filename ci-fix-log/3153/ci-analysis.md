# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11（部分匹配）
- 新模式标题: 根目录文档路径校验失败
- 新模式症状关键词: Path Error, expected path, appstore, README.md, update.py

## 根因分析

### 直接错误
```
2026-07-12 15:33:08,211-.../update.py[line:356]-INFO: Difference: [
    "README.en.md",
    "README.md"
]
...
2026-07-12 15:33:13,075-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档更新，无任何镜像构建文件变更），但 CI 的 appstore 发布规范预检 (`update.py`) 对所有变更文件执行路径校验，要求文件路径符合镜像目录结构规范（如 `{category}/{image}/{version}/{os-version}/...`）。根目录下的 README 文件不匹配任何镜像目录路径模板，被判定为 `[Path Error]`。

### 与 PR 变更的关联
**直接相关**。PR 的改动内容就是更新 `README.md` 和 `README.en.md` 中的可用基础镜像 tag 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目）。CI 对这两个被修改的文件执行 appstore 路径校验，但它们位于仓库根目录而非任何镜像子目录，触发校验失败。PR 本身没有代码或构建问题——问题出在 CI 的校验逻辑对纯文档变更缺乏豁免机制。

## 修复方向

### 方向 1（置信度: 中）
CI 的 `update.py` 在 `line:273` 附近的 appstore 规范检查未区分"镜像相关文件"和"仓库根目录文档"。需要在检查逻辑中增加前置过滤：若变更文件不在任何镜像场景子目录（`AI/`、`Bigdata/`、`Database/`、`Cloud/`、`HPC/`、`Storage/`、`Others/`、`Distroless/`、`Base/`）下，则跳过路径校验。此类文件（如根目录 README）属于仓库元文档，不应受 appstore 发布规范约束。

### 方向 2（置信度: 低）
若 CI 设计上要求所有 PR 都必须通过 appstore 检查且无法豁免，则此 PR 的变更方式需要调整——例如在 PR 中除了文档修改外，同时附带一个符合规范的镜像相关变更，使检查通过。但这显然不合理，不建议采用。

## 需要进一步确认的点
1. `update.py:273` 前后的完整检查逻辑：确认是否有现成的文件路径过滤机制（如按目录前缀白名单跳过），若有则可直接利用。
2. 该项目 CI 是否已有"纯文档 PR 自动跳过 appstore 检查"的机制——若有但未生效，则为配置问题。
3. 同类历史 PR（如纯 README 修改）此前是否也遇到同样的 CI 失败，以确认这是新引入的问题还是一直存在的限制。
