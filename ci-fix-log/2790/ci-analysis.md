# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 根级文件路径校验异常
- 新模式症状关键词: Path Error, The expected path should be, README, appstore, specification errors

## 根因分析

### 直接错误
```
2026-06-30 11:28:09,089-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范检查工具 (`update.py`) 对 PR 中变更的文件进行路径校验，将 `README.md` 的期望路径计算为 `/README.md`，但字符串比较未能正确匹配（可能因缺少/多余前导 `/` 或路径归一化逻辑有缺陷），导致两个根级 README 文件均被标记为 `[Path Error]` 并判定失败。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 中 "可用镜像的 Tags" 表格内容（更新 24.03-lts-sp2 → sp3，新增 25.09、sp3、sp2 行），不涉及路径变更、新增文件、或删除文件。失败由 CI 规范检查工具的路径校验逻辑触发，**与 PR 的具体代码内容无关**——即使 PR 只改动 README 中的一个字符，该检查仍会因路径不匹配而失败。

## 修复方向

### 方向 1（置信度: 低）
CI 工具 `eulerpublisher/update/container/app/update.py` 第 273 行附近的路径校验逻辑对根级文件（如 `README.md`、`README.en.md`）的期望路径计算存在 bug。需检查该脚本中被变更文件的路径与期望路径的比较逻辑：根级文件应被排除在 appstore 路径规范检查之外，或在比较时统一添加/移除前导 `/` 以确保字符串一致性。

### 方向 2（置信度: 低）
该 CI job 的检查本不应在纯 README 文档变更的 PR 上运行——可能是 CI pipeline 的 trigger 条件过于宽泛，未根据 PR diff 内容跳过不相关的规范检查。如果 PR 仅变更根级文档文件而不涉及任何镜像目录，检查应被跳过。

## 需要进一步确认的点
1. `eulerpublisher` 仓库中 `update.py` 第 222-273 行（`_check_specification` 或同类函数）的完整实现逻辑：它如何为每个变更文件计算期望路径，以及为何 `README.md`（实际路径本身即为 `README.md`，等同于 `/README.md`）仍被判定为不匹配。
2. 该 CI 检查的历史行为——之前的 PR 是否也有根级 README 文件变更且通过了该检查？如果历史上有通过的案例，则问题可能出在 `eulerpublisher` 工具本身的版本更新或参数变更上。
3. `update.py:356` 行输出了 `Difference: ["README.en.md", "README.md"]`——这表明工具已正确识别出这两个文件是 PR 的变更文件。需确认工具在后续的期望路径计算中，是否将根级文件错误地归类为"镜像目录下的文件"并套用了错误的路径模板。
