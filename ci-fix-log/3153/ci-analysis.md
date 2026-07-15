# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-.../update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检（`update.py`）对仓库根目录的 `README.md` 文件执行了应用镜像发布规格校验。`README.md` 是仓库的主文档文件（非应用镜像入口），不在 appstore 的 `{category}/{image}/{version}/{os-version}/` 目录规范内，校验工具因此报告 `[Path Error]`。

### 与 PR 变更的关联
**PR 变更不直接触发该失败。** PR 仅修改了 `README.md` 和 `README.en.md` 中的可用基础镜像 tags 表格（更新 latest 指向、补充遗漏版本条目），属于纯文档修正。CI 流水线中的 appstore 发布规范校验逻辑未将根目录文档文件排除在校验范围外，导致文档变更被当作应用镜像条目进行路径格式检查，产生误报。该失败与 PR 代码变更的正确性无关。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线的 appstore 校验工具（`eulerpublisher/update/container/app/update.py`）应在运行规范检查前过滤掉仓库根目录的非应用镜像文件（如 `README.md`、`README.en.md`）。具体来说，在 `_parse_image_info` 或 diff 文件遍历阶段增加路径前缀过滤逻辑，只对位于 `Bigdata/`、`AI/`、`Storage/`、`Database/`、`Cloud/`、`HPC/`、`Distroless/`、`Others/` 等应用场景目录下的文件执行 appstore 路径格式校验。

### 方向 2（置信度: 低）
若上述方向 1 不可行（CI 工具改动受限），可考虑在 `image-list.yml` 或 CI 配置中将 `README.md`、`README.en.md` 等根目录文档文件显式列入排除清单（whitelist/ignorelist），使校验阶段跳过这些文件。

## 需要进一步确认的点
1. 需确认 `update.py` 中 diff 文件列表的来源——是直接比较 branch diff，还是经过某种过滤规则。日志仅显示 `Difference: ["README.md"]`，未揭示为何该文件被纳入 appstore 校验范围。
2. 需确认是否存在同一 CI 流水线的其他下游 job（如 aarch64 架构构建 job）也有额外失败，当前提供的日志仅覆盖 x86-64 job 的 appstore 预检阶段。
3. 需在 `eulerpublisher` 代码库中查看 `update.py:273` 附近的校验逻辑以及 `format.py` 中的 `_parse_image_info` 函数（参考模式11 中 PR #2751 的案例），确认路径校验的触发条件。

## 修复验证要求
（本次分析未涉及对第三方/上游源文件的正则 patch，无需额外验证步骤。）
