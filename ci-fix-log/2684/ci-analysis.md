# CI 失败分析报告

## 基本信息
- PR: #2684 — 【自动升级】oozie容器镜像升级至5.2.1版本.
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Maven仓库证书过期
- 新模式症状关键词: PKIX path validation failed, CertPathValidatorException, validity check failed, NotAfter, releases.java.net, maven.java.net, txw2, jax-maven-plugin

## 根因分析

### 直接错误
```
#8 573.0 [ERROR] Failed to execute goal com.github.davidmoten:jax-maven-plugin:0.1.6:xjc (default) on project oozie-fluent-job-api: Execution default of goal com.github.davidmoten:jax-maven-plugin:0.1.6:xjc failed: Plugin com.github.davidmoten:jax-maven-plugin:0.1.6 or one of its dependencies could not be resolved: Failed to collect dependencies at com.github.davidmoten:jax-maven-plugin:jar:0.1.6 -> com.github.davidmoten:jax-maven-plugin-core:jar:0.1.6 -> com.sun.xml.ws:jaxws-tools:jar:2.3.1 -> com.sun.xml.ws:jaxws-rt:jar:2.3.1 -> com.sun.xml.ws:policy:jar:2.7.5 -> org.glassfish.jaxb:txw2:jar:2.4.0-b180608.0325: Failed to read artifact descriptor for org.glassfish.jaxb:txw2:jar:2.4.0-b180608.0325: Could not transfer artifact org.glassfish.jaxb:txw2:pom:2.4.0-b180608.0325 from/to releases.java.net (http://maven.java.net/content/repositories/releases/): PKIX path validation failed: java.security.cert.CertPathValidatorException: validity check failed: NotAfter: Wed Apr 01 23:59:59 UTC 2026 -> [Help 1]
#8 573.0 ERROR, Oozie distro creation failed
#8 ERROR: process "/bin/sh -c git clone -b release-${VERSION} https://github.com/apache/oozie.git &&     cd oozie/bin &&     ./mkdistro.sh -DskipTests" did not complete successfully: exit code: 255
```

### 根因定位
- 失败位置: `Bigdata/oozie/5.2.1/24.03-lts-sp3/Dockerfile:16-18`（`./mkdistro.sh -DskipTests` 步骤）
- 失败原因: Oozie 5.2.1 的 Maven 构建依赖 `org.glassfish.jaxb:txw2:jar:2.4.0-b180608.0325`，该制品的版本号含预发布后缀 `-b180608.0325`，仅托管在 `releases.java.net`（即 `maven.java.net`）仓库。该仓库的 SSL 证书已于 **2026-04-01 23:59:59 UTC** 过期，构建日期 2026-06-22 时 Java 证书路径验证拒绝连接，Maven 无法下载 POM 描述符，导致依赖解析失败。

### 与 PR 变更的关联
PR 变更仅新增了一个 Dockerfile 来构建 Oozie 5.2.1 以及更新相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中指定的构建命令（`git clone` + `./mkdistro.sh -DskipTests`）语法正确，问题出在上游 Apache Oozie 项目的 Maven 构建系统引用了已过期的外部仓库 `releases.java.net`。**该失败与 PR 的代码变更无关**，属于上游项目的外部依赖基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
在 Dockerfile 中 `./mkdistro.sh` 执行前，通过 Maven 配置排除已过期的 `releases.java.net` 仓库，或将该仓库的 URL 从 `http` 替换为 `https`（若上游提供有效证书的 HTTPS 端点）。具体为：在克隆 Oozie 源码后，修改其根目录下的 `pom.xml`（或 Maven settings），移除对 `maven.java.net` 的引用，使 Maven 仅从 `central`（Maven Central）解析依赖。但需注意 `txw2:2.4.0-b180608.0325` 这个特定版本在 Maven Central 可能不存在，可能需要将依赖版本回退到 `2.3.1`（Maven Central 有该版本）。

### 方向 2（置信度: 低）
在 Dockerfile 的 `RUN` 步骤中，先手动用 `mvn dependency:get` 或 `wget` 从可访问的镜像源下载 `txw2:2.4.0-b180608.0325` 的 POM 和 JAR，安装到本地 Maven 仓库（`~/.m2/repository`），然后再执行 `./mkdistro.sh`。

## 需要进一步确认的点
1. **上游 Oozie 5.2.1 的 `pom.xml` 中 `releases.java.net` 仓库的具体配置位置**：需确认是在根 `pom.xml`、`bin` 目录下的配置文件、还是 `mkdistro.sh` 脚本中引用的 settings 文件中。需要拉取 `https://github.com/apache/oozie` 的 `release-5.2.1` 分支确认。
2. **`txw2:2.4.0-b180608.0325` 是否在 Maven Central 或其他可用仓库中存在**：若 Maven Central 有该版本，Maven 本应从 `central` 下载成功。日志显示 Maven 在 `central` 查找失败后才回退到 `releases.java.net`，说明 Maven Central 没有此版本。需确认是否可以替换为 Maven Central 存在的版本（如 `txw2:2.3.1`）。
3. **该问题是否影响已有 Oozie 版本的构建**：如 `5.2.1/24.03-lts-sp1` 是否也会因同样的仓库过期而失败，需确认是否为仅 24.03-lts-sp3 的新增构建触发，还是所有 Oozie 构建均受影响。
