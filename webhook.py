import pymysql
from pymysql.converters import escape_string
from pymysql.cursors import DictCursor
from flask import Flask, request
import json
import requests
import urllib.parse
import stream_gears
app = Flask(__name__)
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(2)
import logging
logging.basicConfig(level=logging.INFO)

CQHTTP_API_URL = ''
GROUP_ID = ''
TOKEN = ''
UPLOAD_ROOMS = [25206807]

def execute(sql):
    try:
        conn = pymysql.connect(host='localhost', port=3306, user='root',
                       passwd='root', db='bakie', charset='utf8mb4')
        cur = conn.cursor(DictCursor)
        cur.execute(sql)
        conn.commit()
        cur.close()
        return cur.fetchall()
    except Exception as e:
        app.logger.info(e)
        conn.rollback()
        return


@app.route("/webhook", methods=['POST'])
async def recvMsg():
    event = json.loads(request.get_data().decode("utf-8"))
    app.logger.info("event:"+event["type"])
    app.logger.info(event)
    msg = ""
    qbot_notify = False
    room_id = event["data"]['room_info']["room_id"] if 'room_info' in event["data"] else (event["data"]['room_id'] if "room_id" in event["data"] else 0)
    if room_id != 0 and not (event["type"] == "RecordingStartedEvent" or event["type"] == "LiveBeganEvent"):
        room_raw = execute("select * from room_info where room_id = '{}' order by id desc".format(room_id))
        room_info = json.loads(room_raw[0]['json'])
        sql_id = room_raw[0]['id']
    if event["type"] == "LiveBeganEvent":
        username = event["data"]["user_info"]["name"]
        roomid = event["data"]["room_info"]["room_id"]
        roomurl = 'https://live.bilibili.com/' + str(roomid)
        title = event["data"]["room_info"]["title"]
        app.logger.info("I:" + username + "开播了")
        execute("insert into room_info(room_id,json,time) values('{}','{}','{}')".format(
            room_id, escape_string(json.dumps(event["data"]["room_info"], ensure_ascii=False)),
            escape_string(event['date'])))
        r = requests.get(event["data"]["room_info"]["cover"])
        with open('./' + room_id + '-' + event['date'].split(":")[0] +'.jpg','wb') as f:
            f.write(r.content)
        msg = username + '开播了\n标题:' + title + '\n' + roomurl
    elif event["type"] == "LiveEndedEvent":
        username = event["data"]["user_info"]["name"]
        app.logger.info("I:" + username + "下播了")
        msg = username + '下播了'
        room_info['live_status'] = 0
        execute("update room_info set json = '{}' where room_id = '{}' and id = {}".format(escape_string(json.dumps(room_info, ensure_ascii=False)), room_id, sql_id))
        qbot_notify = False
    elif event["type"] == "RecordingStartedEvent":
        title = event["data"]["room_info"]["title"]
        room_id = event["data"]["room_info"]["room_id"]
        app.logger.info("I:开始录制 {}-{}的直播".format(title,room_id))
        msg = "开始录制 {}-{}的直播".format(title,room_id)
        qbot_notify = False
    elif event["type"] == "RecordingFinishedEvent":
        title = event["data"]["room_info"]["title"]
        room_id = event["data"]["room_info"]["room_id"]
        app.logger.info("I:完成 {}-{} 的直播录制".format(title,room_id))
        msg = "完成 {}-{} 的直播录制".format(title,room_id)
    elif event["type"] == "RecordingCancelledEvent":
        username = event["data"]["user_info"]["name"]
        app.logger.info("I:取消" + username + "的直播录制")
        msg = '取消' + username + '的直播录制'
        qbot_notify = False
    elif event["type"] == "VideoFileCompletedEvent":
        path = event["data"]["path"]
        app.logger.info("I:视频已保存于" + path)
        msg = "视频已保存于" + path
        if not "video_file" in room_info:
            room_info["video_file"] = [path]
        else:
            room_info["video_file"].append(path)
        execute("update room_info set json = '{}' where room_id = '{}' and id = '{}'".format(
            escape_string(json.dumps(room_info, ensure_ascii=False)),room_id,sql_id))
        qbot_notify = False
    elif event["type"] == "VideoPostprocessingCompletedEvent":
        path = event["data"]["path"]
        app.logger.info("I:视频处理完成，保存于" + path)
        msg = "视频处理完成，保存于" + path
        if not "video_process" in room_info:
            room_info["video_process"] = [path]
        else:
            room_info["video_process"].append(path)
        execute("update room_info set json = '{}' where room_id = '{}' and id = '{}'".format(
            escape_string(json.dumps(room_info, ensure_ascii=False)),room_id,sql_id))
        qbot_notify = False
        if (len(room_info["video_file"]) == len(room_info["video_process"]) and room_id in UPLOAD_ROOMS and not room_info['live_status']):
            app.logger.info("start upload")
            executor.submit(stream_gears.upload,
                room_info["video_process"],
                "./cookies.json", #cookies
                "【直播回放】" + room_info["title"] + " " + room_raw[0]['time'].split(":")[0] + "点场",
                27,
                "直播回放", # tag
                2,
                "https://live.bilibili.com/XXXX", #copyright
                "XXXX直播间：https://live.bilibili.com/XXXX", # introduction
                "此为自动直播上传，如有问题请及时私信", # dynamic
                "./" + room_id + '-' + room_raw[0]['time'].split(":")[0] + ".jpg", #cover
                None, #延迟发布
                None, #自动选择上传线路
                3,
            )
    elif event["type"] == "SpaceNoEnoughEvent":
        app.logger.info("W:磁盘空间不足")
        msg = '警告：磁盘空间不足，请及时处理！'
    elif event["type"] == "Error":
        app.logger.info("E:程序发生错误")
        msg = '警告：程序出现异常，请及时检查！'
    if (qbot_notify):
        r = requests.get(CQHTTP_API_URL + '/send_group_msg?access_token=' + TOKEN + '&group_id=' + GROUP_ID + '&message=' + urllib.parse.quote(msg) )
        app.logger.info(r.text)
    return msg


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=27817)
