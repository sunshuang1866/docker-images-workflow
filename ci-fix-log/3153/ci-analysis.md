# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (已有模式，无需填写)
- 新模式症状关键词: (已有模式，无需填写)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 appstore 发布规范校验工具（`update.py`）在扫描 PR diff 时，检测到根目录 `README.md` 发生变更，但该工具进行路径匹配时要求路径格式携带前导斜杠（`/README.md`），而 Git diff 中根目录文件的路径不带前导斜杠（`README.md`），导致字符串比对不匹配，校验失败。

### 与 PR 变更的关联
PR 仅修改了两个根目录 README 文件（`README.md`、`README.en.md`），更新了基础镜像可用的 Tags 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 等条目）。变更内容本身无问题，但触发了 CI 工具对根目录文件路径的格式校验逻辑。失败与 PR 的文档内容修改无直接因果关系，与 CI 工具的路径字符串比对方式有关。

## 修复方向

### 方向 1（置信度: 中）
CI 校验工具 `update.py` 在进行 appstore 规范路径校验时，对 Git diff 产出的路径（不带前导 `/`）与期望路径格式（带前导 `/`）做了直接字符串比对，未做路径归一化处理。应在 `update.py` 内的路径比对逻辑中统一对两边的路径进行归一化（如统一去除或添加前导 `/`），使根目录文件路径格式一致后再比对。

### 方向 2（置信度: 低）
CI 工具可能未将根目录 `README.md` 注册为其 appstore 发布规范中的合法变更文件范围。若该工具仅设计用于校验应用镜像目录内的文件变更，根目录 README 不在其预期的校验白名单中，则错误消息可能是变相的"不在允许变更范围内"。此方向可能性较低，因为错误消息明确写的是路径格式问题而非文件不在白名单。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中第 273 行附近路径校验的具体实现逻辑（是直接字符串比对还是已做了归一化处理）。
- 该 CI 校验步骤是否应适用于纯文档（根目录 README）变更 PR，还是应跳过对此类文件路径的校验。
- 历史上是否有其他仅修改根目录 README 的 PR 也触发了同样的校验失败（可对比模式 11 中 `.claude/README.md` 相关案例）。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本次失效涉及 CI 工具内部逻辑，不涉及第三方/上游源文件的正则匹配。）
