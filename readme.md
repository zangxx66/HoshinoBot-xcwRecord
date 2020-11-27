**仅在HoshinoBot测试通过，如果你是yobot使用者或其他bot请自行改造**
# xcw再骂我一次（）
## 食用
1.将xcw文件夹放入modules目录下，并在config里启用该模组  
2.将record/mawo文件夹放在HoshinoBot/res/record根目录下  
**[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)0.9.28及以上版本请自行安装依赖ffmpeg，0.9.28以下版本仅支持amr格式但不依赖ffmpeg**
## 指令
|指令|说明|
|-----|-----|
|@你的机器人 骂我|仅支持群聊|  

# 去你大爷的哔哩哔哩小程序
#### [cq-picsearcher-bot](https://github.com/Tsuk1ko/cq-picsearcher-bot)的python实现
## 食用
1.安装requirements.txt  
2.将pulipuli文件夹放入modules目录下，并在config里启用该模组  
3.将img文件夹下的文件放入HoshinoBot/res/img根目录下  
4.仅支持识别小程序和链接分享  
## 指令  
支持在线搜索视频    
|指令|说明|
|-----|-----|
|搜索+关键词|仅支持群聊，默认120秒限制防止过多请求服务器|  

# 网易点歌台
## 食用
**只支持[cqhttp-maial](https://github.com/yyuueexxiinngg/cqhttp-mirai)0.2.3及以上版本**  
**只支持[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)0.9.22及以上版本**  

将neteasemusic文件夹放入modules目录下，并在config里启用该模组  
## 指令  
|指令|说明|
|-----|-----|
|点歌+歌名或关键词|只返回搜索结果第一条数据，对于重名的歌曲目前做不到精确查询|  

# jjc查询  
## 食用
1.备份原有的priconne/arena，如有异常可方便还原  
2.将arena放入priconne文件夹内  

新增本地存储功能，默认启用，无需配置，以防作业网国内线路故障  
本地存储原理：优先查询本地，本地无该条记录则请求作业网，请求成功将会记录到本地  
本地存储路径：~/.hoshino/arena_cache.db（此为Linux下的路径，未在Windows测试）

## 指令  
|指令|说明|
|-----|-----|
|（b\|日\|台）怎么拆+空格+阵容|与原hoshino指令相同，若查询异常则会返回错误码，方便上报维护组|  
|查询jjc错误码|供请求失败时查询对应错误码信息|  
|刷新作业+空格+阵容|刷新作业，获取最新的数据|  

# 聊天
## 食用  
1.将groupchat文件夹放入modules目录下， 并在config里启用该模组  
2.将自己收集的龙王表情包放入HoshinoBot/res/img/longwang目录下  

**只支持[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)0.9.25及以上版本**  

## 指令  
|指令|说明|
|-----|-----|  
|迫害龙王||  
|当前龙王||
|龙王排行榜||
|设置管理员(at)|at要设置管理员的人，bot需要有群主权限|  
|取消管理员(at)|同上|  
|设置群名+想设置的名字|需要群主权限|  
|戳一戳(at)|at想要bot戳的人（直接戳bot有惊喜）|  
|申请头衔+想要的头衔|需要群主权限|  
|(at)夸我||
|(at)来点鸡汤||
|(at)今日一言||
|(at)跟我学+内容|仅支持中英文|
|合刀|计算尾刀补偿时间<br>指令：合刀 刀1伤害 刀2伤害 剩余血量<br>如：合刀 50 60 70|

# PCR无关
最近沉迷FF14的产物  
## 指令  
|指令|说明|
|-----|-----|
|(钓鱼笔记\|钓鱼日记)+需查询的鱼的名字||
|钓鱼区域+地图名称||  

# 补充桃能量  
## 食用
1.将echo文件夹放入modules目录下，并在config里启用该模组  
2.将record/echo文件夹放在HoshinoBot/res/record根目录下  
**[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)0.9.28及以上版本请自行安装依赖ffmpeg，0.9.28以下版本仅支持amr格式但不依赖ffmpeg**
## 指令
|指令|说明|
|-----|-----|
|(at)我爱你||
|(来点桃宝\|来点echo\|来点cfm)|随机桃能量|
|(晚安\|睡了\|睡觉了\|眠了)|来着桃宝的晚安|
|想听生日歌|送上cfm限定生日歌一首|
|爽死了||
|对呀对呀||
|(我好了\|whl)||
|(hso\|好涩噢\|好涩哦\|好色噢\|好色哦)||