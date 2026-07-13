# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档PR误触检测
- 新模式症状关键词: Path Error, The expected path should be, README, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-12 15:33:08,211- update.py[line:356]-INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-07-12 15:33:13,075- update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）将根目录下的文档文件 `README.md` 和 `README.en.md` 纳入了检查范围，但这两个文件不属于任何应用镜像的目录结构（不遵循 `{category}/{image}/{version}/{os-version}/Dockerfile` 等路径规范），被报告为 [Path Error]，预期路径为 `/README.md`。

### 与 PR 变更的关联
- **无关。** 此 PR 仅修改了两个 README 文档文件（更新可用基础镜像的 tag 列表和对应的下载链接），属于纯文档变更。
- `README.en.md`：将 latest 标签从 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`，新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 标签。
- `README.md`：同上内容的中文版修改。
- CI 的 appstore 发布规范预检逻辑在仅有文档变更的 PR 上产生了误报——它检测到变更文件后，对这些文件执行了应用镜像路径规范校验，但根目录文档文件本就不应属于 appstore 镜像发布管线的检查范围。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线中 `eulerpublisher/update/container/app/update.py` 的 appstore 发布规范预检逻辑应区分"文档/配置类文件"和"应用镜像文件"，仅对镜像相关目录下的文件执行路径规范校验。根目录下的 `README.md`、`README.en.md`、`.claude/` 等纯文档/配置变更应被跳过。

### 方向 2（置信度: 低）
如果 CI 检查器的 `expected path = /README.md` 是由于仓库根目录缺少 `README.md` 文件或文件路径解析异常导致，则需要确认 CI 克隆的仓库路径与实际文件结构的映射关系是否正确。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 附近的 appstore 预检逻辑具体如何判断哪些文件属于"应检查文件范围"，以及为何根目录 README 文件未被过滤。
2. 该 CI 流水线是否在历史上曾正确放行过纯文档类 PR，对比确认是否存在近期更新引入了该回归。
3. 与历史类似案例（PR #2512 中 `.claude/` 路径被判定为路径错误）的关联——可能暗示此检查对"非镜像类根目录文件"的处理存在系统性缺陷，而非单次偶发。

## 修复验证要求
本报告结论为 infra-error（CI 基础设施问题），code-fixer 无需对 PR 代码进行修改。若需修复 CI 流水线本身，应由 CI 平台维护人员修改 `update.py` 中 appstore 预检逻辑的文件过滤规则，使其排除根目录非镜像类文件（`README.md`、`README.en.md`、`.claude/` 等）。
