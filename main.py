import os
from loguru import logger
import warnings
import asyncio
import aiohttp
import yaml
import itertools
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src import BiliUser

log = logger.bind(user="B站粉丝牌助手")
__VERSION__ = "0.3.5"

warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)
os.chdir(os.path.dirname(os.path.abspath(__file__)).split(__file__)[0])
try:
    with open('config/users.yaml', 'r', encoding='utf-8') as f:
        users = yaml.load(f, Loader=yaml.FullLoader)
        assert users['ASYNC'] in [0, 1], "ASYNC参数错误"
        assert users['LIKE_CD'] >= 0, "LIKE_CD参数错误"
        assert users['SHARE_CD'] >= 0, "SHARE_CD参数错误"
        assert users['DANMAKU_CD'] >= 0, "DANMAKU_CD参数错误"
        assert users['WATCHINGLIVE'] in [0, 1], "WATCHINGLIVE参数错误"
        assert users['WEARMEDAL'] in [0, 1], "WEARMEDAL参数错误"
        config = {
            "ASYNC": users['ASYNC'],
            "LIKE_CD": users['LIKE_CD'],
            "SHARE_CD": users['SHARE_CD'],
            "DANMAKU_CD": users['DANMAKU_CD'],
            "WATCHINGLIVE": users['WATCHINGLIVE'],
            "WEARMEDAL": users['WEARMEDAL'],
            "SIGNINGROUP": users.get('SIGNINGROUP', 2),
            "PROXY": users.get('PROXY'),
        }
except Exception as e:
    log.error(f"读取配置文件失败,请检查配置文件格式是否正确: {e}")
    exit(1)


@log.catch
async def main():
    messageList = []
    session = aiohttp.ClientSession()
    try:
        log.warning("当前版本为: " + __VERSION__)
        resp = await (
            await session.get("http://version.fansmedalhelper.1961584514352337.cn-hangzhou.fc.devsapp.net/")
        ).json()
        if resp['version'] != __VERSION__:
            log.warning("新版本为: " + resp['version'] + ",请更新")
            log.warning("更新内容: " + resp['changelog'])
            messageList.append(f"当前版本: {__VERSION__} ,最新版本: {resp['version']}")
            messageList.append(f"更新内容: {resp['changelog']} ")
        if resp['notice']:
            log.warning("公告: " + resp['notice'])
            messageList.append(f"公告: {resp['notice']}")
    except Exception:
        messageList.append("检查版本失败")
        log.warning("检查版本失败")
    initTasks = []
    startTasks = []
    catchMsg = []
    for user in users['USERS']:
        if user['access_key']:
            biliUser = BiliUser(
                user['access_key'], user.get('white_uid', ''), user.get('banned_uid', ''), config
            )
            initTasks.append(biliUser.init())
            startTasks.append(biliUser.start())
            catchMsg.append(biliUser.sendmsg())
    try:
        await asyncio.gather(*initTasks)
        await asyncio.gather(*startTasks)
        messageList = messageList + list(itertools.chain.from_iterable(await asyncio.gather(*catchMsg)))
    except Exception as e:
        log.exception(e)
        messageList.append(f"任务执行失败: {e}")
    [log.info(message) for message in messageList]
    if users.get('SENDKEY', ''):
        await push_message(session, users['SENDKEY'], "  \n".join(messageList))
    await session.close()
    if users.get('MOREPUSH', ''):
        from onepush import notify

        notifier = users['MOREPUSH']['notifier']
        params = users['MOREPUSH']['params']
        await notify(
            notifier,
            title=f"【B站粉丝牌助手推送】",
            content="  \n".join(messageList),
            **params,
            proxy=config.get('PROXY'),
        )
        log.info(f"{notifier} 已推送")


def run(*args, **kwargs):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    log.info("任务结束,等待下一次执行")


async def push_message(session, sendkey, message):
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = {"title": f"【B站粉丝牌助手推送】", "desp": message}
    await session.post(url, data=data)
    log.info("Server酱已推送")


if __name__ == '__main__':
    cron = users.get('CRON', None)
    if cron:
        log.info('使用内置定时器,开启定时任务,等待时间到达后执行')
        schedulers = BlockingScheduler()
        schedulers.add_job(run, CronTrigger.from_crontab(cron), misfire_grace_time=3600)
        schedulers.start()
    else:
        log.info('外部调用,开启任务')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
        log.info("任务结束")
