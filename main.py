import json
import os
from loguru import logger
import warnings
import asyncio
import aiohttp
import itertools
from src import BiliUser

log = logger.bind(user="B站粉丝牌助手")
__VERSION__ = "0.3.5"

warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)
os.chdir(os.path.dirname(os.path.abspath(__file__)).split(__file__)[0])
config={}
try:
    global users
    if os.environ.get("USERS"):
        users = json.loads(os.environ.get("USERS"))
    else:
        import yaml

        with open('config/users.yaml', 'r', encoding='utf-8') as f:
            users = yaml.load(f, Loader=yaml.FullLoader)["USERS"]

            for u in users:
                token = u["access_key"]
                assert u['ASYNC'] in [0, 1], f"用户 {token} ASYNC参数错误"
                assert u['LIKE_CD'] >= 0,  f"用户 {token} LIKE_CD参数错误"
                assert u['SHARE_CD'] >= 0,  f"用户 {token} SHARE_CD参数错误"
                assert u['DANMAKU_CD'] >= 0,  f"用户 {token} DANMAKU_CD参数错误"
                assert u['WATCHINGLIVE'] >= 0,  f"用户 {token} WATCHINGLIVE参数错误"
                assert u['WEARMEDAL'] in [0, 1],  f"用户 {token} WEARMEDAL参数错误"

                config[token] = {
                    "ASYNC": u['ASYNC'],
                    "LIKE_CD": u['LIKE_CD'],
                    "SHARE_CD": u['SHARE_CD'],
                    "DANMAKU_CD": u['DANMAKU_CD'],
                    "WATCHINGLIVE": u['WATCHINGLIVE'],
                    "WEARMEDAL": u['WEARMEDAL'],
                    "SIGNINGROUP": u.get('SIGNINGROUP', 2),
                    "PROXY": u.get('PROXY'),
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
    except Exception:
        messageList.append("检查版本失败")
        log.warning("检查版本失败")
    initTasks = []
    startTasks = []
    catchMsg = []

    for token,conf in config.items():
        if token:
            biliUser = BiliUser(
                token, conf.get('white_uid', ''), conf.get('banned_uid', ''), conf
            )
            initTasks.append(biliUser.init())
            startTasks.append(biliUser.start())
            catchMsg.append(biliUser.sendmsg())
    try:
        await asyncio.gather(*initTasks)
        await asyncio.gather(*startTasks)
    except Exception as e:
        log.exception(e)
        # messageList = messageList + list(itertools.chain.from_iterable(await asyncio.gather(*catchMsg)))
        messageList.append(f"任务执行失败: {e}")
    finally:
        messageList = messageList + list(itertools.chain.from_iterable(await asyncio.gather(*catchMsg)))
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
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    for u in users:
        cron = u.get('CRON', None)
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
