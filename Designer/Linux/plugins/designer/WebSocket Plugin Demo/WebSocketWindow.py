#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2020/12/5
@author: Irony
@site: https://pyqt5.com https://github.com/PyQt
@email: 892768447@qq.com
@file: WebSocketWindow
@description:
"""

import cgitb
import json
import logging
import os
import sys
import zlib
from datetime import datetime

from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, QUrl, QByteArray, QSettings
from PyQt5.QtGui import QPixmap, QTextDocument, QTextCursor
from PyQt5.QtNetwork import QAbstractSocket
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog, QInputDialog, QTextEdit


class WebSocketWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super(WebSocketWindow, self).__init__(*args, **kwargs)
        uic.loadUi('WebSocketTest.ui', self)
        self._param_sep = '\n\n' + '-' * 50
        self._files = []
        self.listWidget.setEnabled(False)

        # 读取配置文件
        setting = QSettings('F:/QtDesigner/Windows/plugins/designer/data/server.ini', QSettings.IniFormat)
        port = setting.value('ws_port', 55441)

        self.editAddress.setPlaceholderText('比如：ws://127.0.0.1:%s' % port)
        self.editAddress.setText('ws://127.0.0.1:%s' % port)

        self._socket = QWebSocket(parent=self)
        self._socket.connected.connect(self.onConnected)
        self._socket.disconnected.connect(self.onDisconnected)
        self._socket.binaryMessageReceived.connect(self.onBinaryMessageReceived)
        self._socket.textMessageReceived.connect(self.onTextMessageReceived)
        self._socket.error.connect(self.onError)

    @pyqtSlot()
    def on_buttonConnect_clicked(self):
        # 连接
        url = self.editAddress.text().strip()
        if not url or not url.startswith('ws://'):
            return
        self.editAddress.setEnabled(False)
        self.buttonConnect.setEnabled(False)
        self._socket.open(QUrl(url))

    @pyqtSlot()
    def on_buttonSend_clicked(self):
        # 执行命令
        code = self.textEditParams.toPlainText().split(self._param_sep)[0].strip().strip('\n')
        if not code:
            return
        try:
            code = json.loads(code)
            self._sendCode(code)
        except Exception as e:
            self.textBrowserApi.append('<font color=red>{0}</font>'.format(str(e)))

    def on_textBrowserApi_textChanged(self):
        self.textBrowserApi.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)

    def on_checkBoxWrap_toggled(self, toggled):
        # 自动换行
        self.textBrowserApi.setLineWrapMode(QTextEdit.WidgetWidth if toggled else QTextEdit.NoWrap)

    def on_listWidget_itemClicked(self, item):
        index = self.listWidget.row(item)
        if index == 0:
            self.onOpenFiles()
        elif index == 1:
            self.onCloseFiles()
        elif index == 2:
            self.onWindowInfo()
        elif index == 3:
            self.onWindowCode()
        elif index == 4:
            self.onWindowScreenShot()
        elif index == 5:
            self.onSetStyleSheet()
        elif index == 6:
            self.onSetProperties()
        elif index == 7:
            self.onSendLogs()

    def setParams(self, param, doc=''):
        # 设置参数显示
        self.textEditParams.clear()
        self.textEditParams.appendPlainText(json.dumps(param, indent=4))
        if doc:
            self.textEditParams.appendPlainText(self._param_sep)
            self.textEditParams.appendPlainText(doc)
        self.textEditParams.moveCursor(QTextCursor.Start, QTextCursor.MoveAnchor)

    def onOpenFiles(self):
        # 打开文件
        files, _ = QFileDialog.getOpenFileNames(self, self.tr('打开'), '', self.tr('设计师UI文件(*.ui)'))
        if not files:
            return
        # 一定要把\\转为/
        self._files = [f.replace('\\', '/') for f in files]
        self.setParams({'method': 'openFiles', 'files': self._files},
                       '\n\nfiles=[...] 需要打开的UI文件路径数组，必须把路径中的\\替换为/')

    def onCloseFiles(self):
        # 关闭文件
        item, ok = QInputDialog.getItem(
            self, self.tr('关闭方式'),
            self.tr('all=true关闭所有打开的文件，忽略files参数\n否则只关闭files参数指定的文件'),
            ['True', 'Files'], 0, False)
        if not ok:
            return
        if item == 'True':
            self.setParams({'method': 'closeFiles', 'all': True},
                           '\n\nall=true 关闭所有打开的文件并忽略 files参数\nfiles=[...] 只关闭files参数指定的文件')
            return
        if self._files:
            self.setParams({'method': 'closeFiles', 'files': self._files},
                           '\n\nall=true 关闭所有打开的文件并忽略 files参数\nfiles=[...] 只关闭files参数指定的文件')

    def onWindowInfo(self):
        # 获取窗口信息
        item, ok = QInputDialog.getItem(
            self, self.tr('获取类型'), self.tr('all=true所有属性和信号槽连接（包括继承）'),
            ['True', 'False'], 0, False)
        if not ok:
            return
        self.setParams({'method': 'getObjectInfos', 'all': item == 'True'},
                       '\n\nall=true 获取所有属性和信号槽连接（包括继承）\nall=false 获取该类自身的属性和信号槽连接')

    def onWindowCode(self):
        # 获取窗口代码
        item, ok = QInputDialog.getItem(
            self, self.tr('代码类型'),
            self.tr('xml\nc++,cpp,c\npyqt5\npyside2'),
            ['xml', 'cpp', 'pyqt5', 'pyside2'], 0, False)
        if not ok:
            return
        self.setParams({'method': 'getUiCode', 'type': item}, '\n\nxml cpp pyqt5 pyside2')

    def onWindowScreenShot(self):
        # 获取窗口截图
        item, ok = QInputDialog.getItem(
            self, self.tr('截取类型'),
            self.tr('all=所有打开的窗口\nmain=整个设计师窗口\ncurrent或其他值则为当前窗口'),
            ['all', 'main', 'current'], 0, False)
        if not ok:
            return
        self.setParams({'method': 'getScreenShot', 'type': item, 'callback': 'doViewImages'},
                       '\n\ntype=all 截取所有打开的UI文件的界面图\ntype=main 截取整个设计师窗口\ntype=current或其他值则截取当前窗口\ncallback=function '
                       '可选回调函数跟随服务端返回值里附带（用户客户端自己调用对应的回调函数）\n\n注意: 返回的是Base64编码的PNG图片')

    def onSetStyleSheet(self):
        # 打开测试文件
        path = os.path.abspath('TestUi.ui').replace('\\', '/')
        self._sendCode({'method': 'openFiles', 'files': [path]})
        self.setParams({'method': 'setStyleSheet',
                        'files': {path: {
                            'Form': {'styleSheet': '#Form {background: black;}'}  # 修改样式
                        }}},
                       '\n\n设置对应控件的样式')

    def onSetProperties(self):
        # 打开测试文件
        path = os.path.abspath('TestUi.ui').replace('\\', '/')
        self._sendCode({'method': 'openFiles', 'files': [path]})
        self.setParams({'method': 'setProperties',
                        'files': {path: {
                            'pushButton': {
                                'text': '测试文字',  # 修改文字
                                'geometry': [100, 100, 30, 30],  # 修改位置和大小
                            }
                        }}},
                       '\n\n设置对应控件的样式')

    def onSendLogs(self):
        # 发送日志
        self.setParams({'method': 'sendLog', 'level': logging.INFO, 'msg': 'log message'},
                       '\n\n发送日志\nlevel: 0=NOTSET\nlevel: 10=DEBUG\nlevel: 20=INFO\nlevel: 30=WARNING\nlevel: '
                       '40=ERROR\nlevel: 50=CRITICAL')

    def doViewImages(self, info):
        # 截图回调函数
        for name, value in info.get('data', {}).items():
            try:
                pixmap = QPixmap()
                # 从base64加载图
                pixmap.loadFromData(QByteArray.fromBase64(value.encode()))
                # 显示小图
                self.textBrowserApi.document().addResource(
                    QTextDocument.ImageResource, QUrl('dynamic:/{0}'.format(name)), pixmap.scaledToHeight(512))
                self.textBrowserApi.append('<img src="dynamic:/{0}">'.format(name))
            except Exception as e:
                self.textBrowserApi.append('<font color=red>{0}</font>'.format(str(e)))

    def _sendCode(self, code):
        code = json.dumps(code)
        if self._socket.isValid() and self._socket.state() == QAbstractSocket.ConnectedState:
            # 服务端返回的数据经过zlib压缩
            self._socket.sendTextMessage(code)
        else:
            self.textBrowserApi.append('<font color=red>{0}</font>'.format(self.tr('错误：无法发送网络数据')))

    def onConnected(self):
        self.buttonSend.setEnabled(True)
        self.listWidget.setEnabled(True)
        self.textBrowserApi.append('<font color=black>{0}</font>'.format(self.tr('连接成功')))

    def onDisconnected(self):
        self.editAddress.setEnabled(True)
        self.buttonConnect.setEnabled(True)
        self.listWidget.setEnabled(False)
        self.buttonSend.setEnabled(False)
        self.textBrowserApi.append('<font color=red>{0}</font>'.format(self.tr('连接断开')))

    def onBinaryMessageReceived(self, message):
        try:
            # zlib压缩过后的内容（为了减小带宽传送）
            message = zlib.decompress(message).decode()
        except Exception as e:
            self.textBrowserApi.append('<font color=red>uncompress binary message failed:{0}</font>'.format(e))
            return
        self.onTextMessageReceived(message)

    def onTextMessageReceived(self, message):
        try:
            info = json.loads(message)
            text = json.dumps(info, indent=4 if self.checkBoxFormat.isChecked() else None)
            time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if info.get('type', '') == 'event':
                self.textBrowserEvent.append(time)
                self.textBrowserEvent.append(text)
                self.textBrowserEvent.append('')
            else:
                self.textBrowserApi.append(time)
                self.textBrowserApi.append(text)
                self.textBrowserApi.append('')
            # 调用回调
            callback = info.get('callback', '')
            if callback and hasattr(self, callback) and callable(getattr(self, callback)):
                try:
                    getattr(self, callback)(info)
                except Exception as e:
                    self.textBrowserApi.append('<font color=red>callback({0}) failed:{1}</font>'.format(callback, e))
        except Exception as e:
            self.textBrowserApi.append('<font color=red>json load message failed:{0}</font>'.format(e))
            return

    def onError(self, error):
        self.editAddress.setEnabled(True)
        self.buttonConnect.setEnabled(True)
        self.listWidget.setEnabled(False)
        self.buttonSend.setEnabled(False)
        self.textBrowserApi.append(
            '<font color=red>websocket error:{0} {1}</font>'.format(error, self._socket.errorString()))


if __name__ == '__main__':
    cgitb.enable(format='text')
    app = QApplication(sys.argv)
    w = WebSocketWindow()
    w.show()
    sys.exit(app.exec_())
