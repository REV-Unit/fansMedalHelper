# Docker 部署

## 关于镜像

如果需要浏览镜像参考，请点击 [这里](https://wuxxabcdefg.coding.net/public-artifacts/gitsync/fans_medal_helper/packages)

镜像地址：

```wuxxabcdefg-docker.pkg.coding.net/gitsync/fans_medal_helper/fansmedalhelper```

以下是镜像的 tag 说明：

tag|说明
|:-:|:-:|
latest|最新稳定版本
ci-latest|由 CI 构建出的最新版本
ci-*|由 CI 构建出的历史版本
其余|不带 rc / alpha / beta 后缀的为历史稳定版本

CI 版本的命名规则为

```ci-<commitHash 前 7 位>-<构建序号>```

由于 CI 版本可能存在各种已知或未知的问题，使用它们即代表你能接受这些问题，否则请使用``latest``

## 部署

> 以下以 latest 标签为例

> 关于 docker 命令，请参阅 docker 文档

1. 拉取镜像

    ```shell
    docker pull wuxxabcdefg-docker.pkg.coding.net/gitsync/fans_medal_helper/fansmedalhelper:latest
    ```

2. 创建数据卷

    ```shell
    docker volume create --name FansMedalHelper
    ```

3. 创建容器

    ```shell
    docker run -dit -v FansMedalHelper:/app/fansMedalHelper/config --restart always --name FansMedalHelper wuxxabcdefg-docker.pkg.coding.net/gitsync/fans_medal_helper/fansmedalhelper:latest
    ```

4. 复制配置文件

    ```shell
    docker cp users.yaml FansMedalHelper:/app/fansMedalHelper/config
    ```

5. 查看运行日志

    ```shell
    docker logs FansMedalHelper
    ```

6. 更新容器

    更新容器不会删除原有的配置文件

    1. 首先，停止原容器

        ```shell
        docker stop FansMedalHelper
        ```
    2. 删除原容器

        ```shell
        docker rm FansMedalHelper
        ```

    3. 删除原镜像

        ```shell
        docker rmi wuxxabcdefg-docker.pkg.coding.net/gitsync/fans_medal_helper/fansmedalhelper:latest
        ```

    4. 重新拉取镜像，部署，此处无需重新创建数据卷
