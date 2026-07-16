# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级文档路径校验误报
- 新模式症状关键词: Path Error, expected path, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检阶段）
- 失败原因: PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档变更），但 CI 流水线中的 `update.py` 仍将其纳入 appstore 发布规范检查。该检查期望变更文件位于符合应用镜像目录层级（如 `{category}/{app}/{version}/{os-version}/...`）的路径下，根级 `README.md` 不在其预期路径模式中，被判定为 `[Path Error]`。日志显示工具计算差异时仅识别出 `README.md`，而检查结果描述 "expected path should be /README.md" 表明路径比较可能存在绝对路径 `/` 前缀的规范化问题，或该检查本身不应对根级文档文件执行。

### 与 PR 变更的关联
PR 仅修改了仓库根目录下两个 README 文件的内容（更新支持的镜像 Tags 列表），未涉及任何应用镜像 Dockerfile、meta.yml、image-list.yml 等与 appstore 发布规范直接相关的文件。该失败与 PR 的具体修改内容无关，是 CI 流水线的 appstore 预检步骤对纯文档类 PR 的 false positive。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线的 appstore 发布规范预检应在检测到变更文件列表中仅包含根级文档文件（如 `README.md`、`README.en.md`）时跳过检查或直接判定通过，而非报错退出。这可能需要在 trigger/编排层 job 中增加文件变更类型的过滤逻辑，排除纯文档类 PR。

### 方向 2（置信度: 低）
`update.py` 中的路径比较逻辑可能存在 bug——当文件路径为 `README.md`（无前导 `/`）而期望路径为 `/README.md`（有前导 `/`）时，字符串比较不匹配。如果该检查确实是必须的，可能需要修复路径规范化逻辑。

## 需要进一步确认的点

1. 需要确认 CI 流水线中 appstore 发布规范检查的触发条件——是否所有 PR 都必须通过该检查，还是仅有特定类型的变更才会触发。如果该检查是全局强制项，那么纯文档 PR 的误报问题需要从 CI 端解决。
2. 需要查阅 `eulerpublisher/update/container/app/update.py` 中第 273 行附近的具体检查逻辑，确认路径校验的预期行为。
3. 历史模式中有多个类似案例（如 PR #2512 的 `.claude/agents/README.md` 路径校验），但均不涉及仓库根级 `README.md` 的场景，说明这是一个新的误报模式。

## 修复验证要求
若修复方向涉及 CI 流水线脚本（如 `update.py`）的路径白名单/跳过逻辑，code-fixer 需在提交前验证：
- 本地模拟一个仅修改根级 `README.md` 的 PR，确认修复后该 PR 能通过 appstore 预检
- 验证修复不会导致正常应用镜像 PR 的路径校验被意外跳过
