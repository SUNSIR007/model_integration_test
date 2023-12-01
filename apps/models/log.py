from sqlalchemy import Column, Integer, String, Text

from apps.database import Base


class OperateLog(Base):
    __tablename__ = 'operate_log'

    id = Column(Integer, primary_key=True, doc='日志编号')
    traceId = Column(String(50), doc='链路追踪编号')
    userId = Column(Integer, doc='用户编号')
    module = Column(String(50), doc='操作模块')
    name = Column(String(50), doc='操作名')
    type = Column(Integer, doc='操作分类')
    content = Column(Text, doc='操作明细')
    exts = Column(Text, doc='拓展字段')
    requestMethod = Column(String(10), doc='请求方法名')
    requestUrl = Column(String(100), doc='请求地址')
    userIp = Column(String(20), doc='用户 IP')
    userAgent = Column(String(200), doc='浏览器 UserAgent')
    pythonMethod = Column(String(200), doc='Python 方法名')
    pythonMethodArgs = Column(Text, doc='Python 方法的参数')
    startTime = Column(String(30), doc='开始时间')
    duration = Column(Integer, doc='执行时长，单位：毫秒')
    resultCode = Column(Integer, doc='结果码')
    resultMsg = Column(String(200), doc='结果提示')
    resultData = Column(Text, doc='结果数据')
    userNickname = Column(String(50), doc='用户昵称')
