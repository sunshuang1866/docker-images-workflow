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
2026-07-14 11:28:17,839-...-[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI appstore 预检阶段（`eulerpublisher/update/container/app/update.py:273`）对变更文件 `README.md` 进行路径校验
- 失败原因: CI 的 appstore 发布规范预检工具对根目录 `README.md` 执行路径校验时报错 `[Path Error] The expected path should be /README.md`。该 PR 仅为文档更新（修改 `README.md` 和 `README.en.md` 中基础镜像的可用 Tags 列表），未新增或修改任何 Dockerfile、meta.yml、image-info.yml 等镜像构建文件，appstore 预检对本不应参与的纯文档变更触发了路径校验失败。日志中 `Difference: ["README.md"]` 表明 CI 仅检测到根目录 README 的变更，但 appstore 校验将其纳入了路径合规检查范围并判定为 FAILURE

### 与 PR 变更的关联
PR 变更仅限于更新两个 README 文件中的基础镜像 Tags 列表（将 latest 标签从 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`，并新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 等条目）。PR 本身不包含任何镜像构建相关文件变更，不应当触发 appstore 发布规范预检。该失败与 PR 的实际改动内容无因果关系，属于 CI 基础设施层面的问题：appstore 预检流程被不适当地应用于纯文档更新 PR

## 修复方向

### 方向 1（置信度: 中）
此 PR 为纯文档修改，不涉及镜像发布。若 CI 管线的预期行为是所有 PR 均需通过 appstore 预检，则需在 CI 配置中增加文档类 PR 的白名单豁免规则，使仅修改根目录 README 文件的 PR 跳过 appstore 路径校验。若本次失败为 CI 工具的偶发路径解析异常，则直接重试 CI 流水线即可

### 方向 2（置信度: 低）
若 CI 的 appstore 预检确实要求根目录 README.md 的路径严格匹配 `/README.md` 且当前路径解析存在偏差（例如工具以相对路径 `README.md` 而非绝对路径 `/README.md` 传入校验函数），则需修复 `eulerpublisher/update/container/app/update.py` 中的路径规范化逻辑

## 需要进一步确认的点
1. CI 的 appstore 预检是否对所有 PR 强制执行，还是仅对包含镜像构建文件变更的 PR 触发？需查阅 CI 流水线（Jenkins pipeline / trigger job）中的触发条件配置
2. `update.py` 中路径校验逻辑的具体实现：文件路径比较时是否做了相对路径到绝对路径的归一化处理？
3. `Difference` 列表中仅显示了 `README.md` 而未显示 `README.en.md`，这是否说明 CI 只对特定类型的变更文件触发了预检？
4. 根目录 `README.md` 在 appstore 发布规范中是否被定义为不需要路径校验的文件类型？需查阅 appstore 发布规范的 schema 定义
