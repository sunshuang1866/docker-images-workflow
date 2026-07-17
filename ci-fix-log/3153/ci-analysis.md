# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（部分相似）
- 新模式标题: (不适用 — 已有模式相似但非完全匹配)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

关键上下文：
```
2026-07-16 20:34:19,171-...-INFO: Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI appstore 发布规范预检工具检测到 PR 中变更了仓库根目录下的 `README.md`，并报路径校验失败（`[Path Error] The expected path should be /README.md`）。该 CI 工具本应用于校验应用镜像目录结构下文件的路径合规性（如 `{category}/{image}/{version}/{os-version}/Dockerfile` 格式），但当前 PR 仅对仓库根目录的 `README.md` 和 `README.en.md` 进行了文档修改，并未涉及任何应用镜像目录。CI 预检工具对根目录文件的路径校验行为不合理。

### 与 PR 变更的关联
**关联度：触发但非因果。** PR #3153 的变更仅涉及 `README.md` 和 `README.en.md` 中基础镜像标签列表的更新（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 并调整 URL 链接）。这些内容变更是文档性的、合法的。CI 失败的根本原因并非 PR 改动了错误的内容，而是 CI 的 appstore 预检工具（`update.py`）将所有变更文件（包括根目录 README）纳入 appstore 路径规范校验范围，导致了一个与 PR 本质无关的假阳性失败。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施配置问题——appstore 预检工具对变更文件的路径校验范围过于宽泛，不应将仓库根目录级别的文档文件（`README.md`、`README.en.md`）纳入校验。需在 CI 工具侧（`eulerpublisher/update/container/app/update.py`）添加路径排除规则，使预检仅针对应用镜像目录（如 `AI/`、`Bigdata/`、`Cloud/` 等）下的文件进行路径合规性校验，排除仓库根目录及非镜像目录的文件。

### 方向 2（置信度: 低）
PR 本身可能需要避免在同一次提交中同时修改根目录 README——如果 CI 策略要求将所有涉及 PR 的变更限定在特定的镜像目录范围内。但此方向与 PR 的文档维护目的相悖，不推荐。

## 需要进一步确认的点
1. **CI 工具 `update.py:273` 的完整校验逻辑**：需要查看 `eulerpublisher` 仓库中 `update.py` 第 273 行附近的代码，确认路径校验的范围定义和排除规则，以判断是否为工具 bug 还是设计如此。
2. **同类历史 PR 的 CI 表现**：过往仅修改仓库根目录文件的 PR（如纯 README 文档更新）是否也会触发同样的 appstore 路径校验失败？如果此类 PR 曾通过 CI，说明当前失败可能是由近期 CI 工具更新引入的回归。
3. **`README.en.md` 为何未被标记**：日志中 `Difference` 仅列出 `README.md`，而 PR diff 中 `README.en.md` 也有同等变更。需确认 CI 工具是对文件进行白名单校验（仅校验特定文件名），还是检测逻辑有其他筛选条件。
4. **PR #3184 的角色**：CI 日志显示实际运行由 `PR 3184 [sunshuang1866:fix/3153]` 触发。需要确认 PR #3184 相比 PR #3153 是否有额外的修复改动，以及 PR #3184 是否也包含根目录 README 的变更。

## 修复验证要求
若修复方向涉及修改 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑，code-fixer 必须：
1. 从 eulerpublisher 仓库对应版本获取 `update.py` 完整源码，确认第 273 行附近的校验逻辑；
2. 验证修改后的排除规则对根目录 `README.md` 和 `README.en.md` 确实生效；
3. 确认修改不会放宽对正式应用镜像目录（`AI/`、`Bigdata/`、`Cloud/`、`Database/`、`Distroless/`、`HPC/`、`Others/`、`Storage/`）下文件的路径校验严格度。
