# 修复摘要

## 修复的问题
Dockerfile 中 Python 脚本注释测试方法后未移除对应的未使用 import，导致 Maven checkstyle 检测到 4 个 UnusedImports 违规。

## 修改的文件
- `Cloud/ovirt-engine/4.5.7/24.03-lts-sp3/Dockerfile`: 在 Python 脚本中新增移除未使用 import 语句的逻辑

## 修复逻辑
扩展 Dockerfile 第 35 行的 Python 内联脚本，在注释掉 `testForEnglish`、`testForNonTranslatedLanguage`、`testForNotDefaultLanguage` 三个测试方法后，额外删除因方法被注释而变为无用的 4 条 import 语句：
- `import static org.junit.jupiter.api.Assertions.assertEquals;`
- `import java.util.Locale;`
- `import org.junit.jupiter.api.Test;`
- `import org.ovirt.engine.core.notifier.filter.AuditLogEventType;`

已从上游 `ovirt-engine-4.5.7` tag 获取 `LocalizedMessageHelperTest.java` 验证：
- 该文件中仅有以上 3 个被注释的测试方法和 1 个 `@BeforeEach init()` 方法
- 上述 4 个 import 仅被 3 个被注释的测试方法使用，`init()` 方法使用的是 `Calendar`、`BeforeEach`、`AuditLogSeverity`，这些 import 保留不变
- 正则匹配成功，端到端验证通过

## 潜在风险
无。仅删除与已注释方法直接关联的 import，不影响文件中保留的 `@BeforeEach init()` 方法及其依赖的 import。