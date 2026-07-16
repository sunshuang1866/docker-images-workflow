# 修复摘要

## 修复的问题
无需代码修改。CI 失败是由 CI appstore 路径校验工具（`eulerpublisher/update/container/app/update.py`）的 bug 导致的 infrastructure error，而非 `README.md` 内容有问题。

## 修改的文件
无。`README.md` 内容正确，无需修改。

## 修复逻辑
CI 失败的直接原因是 appstore 路径校验工具将 git diff 输出的相对路径 `README.md` 与内部约定的绝对路径格式 `/README.md` 做精确字符串比较导致不匹配。根目录 `README.md` 不属于应用镜像发布路径范畴（应用镜像在 `Bigdata/`、`AI/` 等子目录下），不应被 appstore 路径规范检查覆盖。

该 bug 位于 `eulerpublisher/update/container/app/update.py` 第 273 行附近，不在本 PR 修改范围（`README.md`）内。需要由 CI 工具维护者在 `update.py` 中修复路径比较逻辑：
- 在路径比较前统一规范化路径格式（统一添加或移除前导 `/`）
- 或增加对仓库根目录级别非镜像文件的跳过过滤逻辑

## 潜在风险
无。`README.md` 未做任何修改，不影响任何功能。