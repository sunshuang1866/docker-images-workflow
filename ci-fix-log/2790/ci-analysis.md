# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（部分匹配）
- 新模式标题: N/A（已有类似模式可参考）

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范检查对根级 `README.md` 进行了路径校验，判定该文件不符合预期路径格式。但 `README.md` 位于仓库根目录，理应匹配 `/README.md` 这一预期路径，日志本身出现了逻辑矛盾。该检查目的为验证镜像发布相关文件的路径规范，而本 PR 仅修改根级文档文件，不应触发此检查。

### 与 PR 变更的关联
PR #2790 仅修改了两个根级 README 文件：
- `README.md`：更新可用镜像 Tags 表格（将 `24.03-lts-sp2` 替换为 `24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目）
- `README.en.md`：同上

PR 未涉及任何 Dockerfile、meta.yml、image-list.yml 或其他镜像构建文件。CI appstore 发布规范检查不应在纯文档 PR 上运行并产生阻塞性失败。

## 修复方向

### 方向 1（置信度: 中）
CI 管道的 appstore 发布规范检查错误地应用到了本 PR。可能原因：
- CI 配置未区分"仅包含根级 README/文档变更的 PR"和"涉及镜像发布的 PR"，对所有 PR 均执行 appstore 路径校验
- appstore 校验工具 `update.py` 对根级 README.md 的路径判定逻辑存在 bug（`/README.md` 理应通过校验但实际失败）

修复思路：CI 层面调整触发条件，使纯文档变更 PR 跳过 appstore 发布规范检查；或排查 `update.py` 中对根级文件路径的判定逻辑。

### 方向 2（置信度: 低）
PR 修改的 README.md 中新增/更新的镜像 Tag（如 `24.03-lts-sp3`、`25.09`）引用的 URL 指向 `openEuler-24.03-LTS-SP3/docker_img/` 等路径，appstore 校验可能对 README 中引用的镜像版本进行了数据库一致性比对，发现不匹配。但从日志的 `[Path Error]` 措辞判断，此可能性较低。

## 需要进一步确认的点
1. **appstore 路径校验逻辑**：需要查阅 `eulerpublisher/update/container/app/update.py` 中路径校验的实现（`line:273` 附近），确认 `[Path Error] The expected path should be /README.md` 的具体含义——为什么根级 README.md 会被判为路径不匹配。
2. **CI 触发条件**：确认 appstore 发布规范检查是否对所有 PR 均执行，是否可以通过变更文件类型（仅 README）自动跳过。
3. **README.en.md 未被检测的原因**：CI 差异检测（`update.py:356`）仅输出 `["README.md"]`，而 PR 同时修改了 `README.en.md`，需要确认是过滤行为还是遗漏。

## 修复验证要求
无需额外验证——此报告将失败归为 `infra-error`，Code Fixer 无需对 Dockerfile 或镜像文件进行修改。若后续排查认定需修改 CI 工具或配置，应由 CI 维护人员操作。
