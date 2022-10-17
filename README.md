# blrec2biliup

通过blrec的WebHook使得录制结束后第一时间上传，同时支持通过CQHTTP报送事件至QQ群

# 使用要求

```
pip install -r requirements.txt
```

使用前请在文件开头和结尾修改相关变量
并在blrec的WebHook设置中添加http://localhost:27817/webhook
cookies.json可参考[biliup-rs](https://github.com/ForgQi/biliup-rs)

MySQL表：
```
-- ----------------------------
-- Table structure for room_info
-- ----------------------------
DROP TABLE IF EXISTS `room_info`;
CREATE TABLE `room_info`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `room_id` int(11) NULL DEFAULT NULL,
  `json` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `time` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 17 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;
```

# TODO

 - 抛弃MySQL
 - 支持不同账号cookies
 - More...

PRs welcome

# Credits

 - [blrec](https://github.com/acgnhiki/blrec)
 - [biliup](https://github.com/biliup/biliup)
 - [biliup-rs](https://github.com/ForgQi/biliup-rs)和封装后的[stream_gears](https://github.com/biliup/stream-gears)提供的接口

 # Used by
 - [巴老师的录播小号](https://space.bilibili.com/1191162350)
