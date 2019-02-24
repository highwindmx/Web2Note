import sys
from datetime import datetime
from PyQt5.QtCore import (QObject, QThread, QTimer, pyqtSignal, pyqtSlot)# 
from PyQt5.QtGui import (QIcon, QPixmap, QImage)
from PyQt5.QtWidgets import (QDialog, QWidget, QLabel, QGridLayout, QPushButton, QSizePolicy)

import pyaudio
import wave
#
#from multiprocessing import (Process, Queue)
# import matplotlib
# matplotlib.use("Qt5Agg")
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas 
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar 
# import matplotlib.pyplot as plt
# import matplotlib.lines as line
# import matplotlib.animation as animation
import numpy as np
import pyqtgraph as pg
# import scipy
import queue
import threading
import time

class Audio:
    def __init__(self, chunksize, rate, channel, format, threshold, save_path):
        self.chunksize = chunksize
        self.rate = rate
        self.channel = channel
        self.format = format
        #
        #self.block = b"" # bytes 类型
        self.record_block_ctr = 0
        self.record_duration = 0
        self.play_block_ctr = 0
        self.play_duration = 0
        self.frames = []
        #
        self.threshold = threshold
        self.save_path = save_path
    
    def getRecordBlock(self, block):
        # 槽函数不要直接和GUI主界面有关系，不然会出现下列错误的
        # QObject::startTimer: Timers cannot be started from another thread
        self.block = block
        #print(len(block))  == 2048 = 2 * chunksize
        self.record_block_ctr += 1
        self.record_duration = self.getDuration(self.record_block_ctr)
        
    def getPlayBlock(self, block):
        self.block = block
        self.play_block_ctr += 1
        self.play_duration = self.getDuration(self.play_block_ctr)
        
    def getRecordFrames(self, frames):
        self.frames = frames
        #dur0 = len(b"".join(self.frames)) / float(self.rate) / 2 # 是 paInt16的关系吗？ 还是不太理解
        #dur1 = self.record_duration
        #print("change")
        #print(dur0, dur1)
    
    def getDuration(self, ctr):
        return ctr * self.chunksize / float(self.rate)
        
class AudioAnalysis(QDialog):
    def __init__(self, mainwin):
        super().__init__()
        self.main_Win = mainwin
        self.snd_record_ctr = 0 
        self.snd_play_ctr = 0
        self.snd_reset_ctr = 0
        self.is_snd_recording = None
        #self.snd_play_tmsp = datetime.now()
       # 
        self.audio = Audio(chunksize=1024, rate=48000, channel=1, format=pyaudio.paInt16
                          ,threshold=500, save_path="test-temp.wav")
        self.initIF()
        self.initSndTreads()
        self.initTimer()

    def initIF(self):
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        icon = QIcon()
        icon.addPixmap(QPixmap("./style/logo3.png"))
        self.setWindowIcon(icon)
        self.setWindowTitle("语音录制与分析")
            
        class WaveSpectrum(pg.PlotWidget):
            def __init__(self, parent=None, maindlg=None):
                super(WaveSpectrum, self).__init__(parent)
                self.main_Dlg = maindlg
                self.audio = self.main_Dlg.audio
                #
                self.item = self.getPlotItem()
                self.item.setMouseEnabled(y=False)
                self.item.setYRange(0,1000)
                range = self.audio.rate/2
                self.item.setXRange(-range,range, padding=0)
                self.axis = self.item.getAxis("bottom")
                self.axis.setLabel("频率（赫兹）")
                
            def updatePlot(self):
                try:
                    data = np.fromstring(self.audio.block, 'int16')
                except Exception as e:
                    print("??",e)
                else:
                    T = 1.0/self.audio.rate
                    N = data.shape[0]
                    Fx = (1./N) * np.fft.fft(data)
                    f = np.fft.fftfreq(N, T)
                    Fx = np.fft.fftshift(Fx)
                    f = np.fft.fftshift(f)
                    self.item.plot(x=f.tolist(), y=(np.absolute(Fx)).tolist(), clear=True)    
    
        self.wave_spectrum_PG = WaveSpectrum(maindlg=self)
        #self.wave_spectrum_PG.enableAutoRange()
        #
        self.result_LB = QLabel(self)
        self.result_LB.setText("欢迎使用")
        self.record_BT = QPushButton(self)
        self.record_BT.setText("开始录音")
        self.record_BT.setMaximumWidth(144)
        self.pause_BT = QPushButton(self)
        #self.pause_BT.setText("暂停")
        #self.pause_BT.setMaximumWidth(48)
        self.play_BT = QPushButton(self)
        self.play_BT.setText("开始播放")
        self.play_BT.setMaximumWidth(144)
        self.reset_BT = QPushButton(self)
        self.reset_BT.setText("重来")
        self.reset_BT.setMaximumWidth(128)
        self.save_BT = QPushButton(self)
        self.save_BT.setText("保存")
        self.save_BT.setMaximumWidth(128)
        self.layout.addWidget(self.wave_spectrum_PG, 0,0, 1,4)
        self.layout.addWidget(self.result_LB, 1,0, 2,4)
        self.layout.addWidget(self.record_BT, 3,0, 2,1)
        #self.layout.addWidget(self.pause_BT, 3,1, 2,1)
        self.layout.addWidget(self.play_BT, 3,1, 2,1)
        self.layout.addWidget(self.reset_BT, 3,2, 2,1)
        self.layout.addWidget(self.save_BT, 3,3, 2,1)

        self.record_BT.clicked.connect(self.click2Record)
        #self.pause_BT.clicked.connect(self.click2Pause)
        self.play_BT.clicked.connect(self.click2Play)
        self.reset_BT.clicked.connect(self.click2Reset)
        self.save_BT.clicked.connect(self.click2Save)
    
    def initSndTreads(self):
        class SoundRecordPlay(QObject):
            audio_record_block_signal = pyqtSignal(bytes)
            audio_record_frame_signal = pyqtSignal(list)
            audio_play_block_signal = pyqtSignal(bytes)
            finished = pyqtSignal()
            #
            def __init__(self, parent=None, maindlg=None):
                super(self.__class__, self).__init__(parent)
                self.main_Dlg = maindlg
                self.audio = self.main_Dlg.audio
                self.format = self.audio.format
                self.channel = self.audio.channel
                self.rate = self.audio.rate
                self.chunksize = self.audio.chunksize
                #
                self.pya = pyaudio.PyAudio()
                self.stream = self.pya.open(format=self.format
                                           ,channels=self.channel
                                           ,rate=self.rate
                                           ,input=True
                                           ,output=True
                                           ,frames_per_buffer=self.chunksize
                                           )
                self.audio_record_block_signal.connect(self.audio.getRecordBlock)
                self.audio_record_frame_signal.connect(self.audio.getRecordFrames)                           
                self.audio_play_block_signal.connect(self.audio.getPlayBlock)    
                self.finished.connect(self.main_Dlg.playFinished)
                # 信号连接就不要反复创建了不然会发出重复信号 很囧对吧。。。                
                
            def create(self):                               
                self.isPaused = True
                self.isStopped = True
                self.record_frames = []
                self.play_frames = self.main_Dlg.audio.frames.copy() # 差点忘了列表是指针复制了。。
                
            def record(self):
                while self.isNewRec:
                    if not self.isStopped:
                        if self.isPaused:
                            self.stream.stop_stream()
                        else:
                            self.stream.start_stream()
                            block = self.stream.read(self.chunksize)
                            self.audio_record_block_signal.emit(block)  
                            self.record_frames.append(block)
                            self.audio_record_frame_signal.emit(self.record_frames)
                    else:
                        self.stream.stop_stream()
                        while not self.isNewRec:
                            continue # hold
                    
            def play(self):
                while (not self.isStopped) and self.play_frames:
                    if not self.isPaused: 
                        self.stream.start_stream()
                        block = self.play_frames.pop(0)
                        self.stream.write(block)
                        self.audio_play_block_signal.emit(block)
                    else:    
                        self.stream.stop_stream()
                        while self.isPaused:
                            continue # hold住
                # for block in self.play_frames:
                #     if not self.isStopped:
                #         if not self.isPaused:
                #             self.stream.start_stream()
                #             self.audio_play_block_signal.emit(block)
                #             # 实时发送r_frames.remove(block) 计算开销太大，播放会卡顿，变通一下
                #             self.stream.write(block)
                #         else:
                #             self.stream.stop_stream()
                #             while self.isPaused:
                #                  continue # hold住
                #     else:
                #         self.stream.stop_stream()
                #         break
                #
                self.stream.stop_stream()                
                self.finished.emit()
            
            def start(self):
                self.isPaused = False
                self.isStopped = False
                self.isNewRec = True
                
            def pause(self):
                self.isPaused = True

            def resume(self):
                self.isPaused = False

            def stop(self):
                self.isStopped = True
                
            def close(self):
                self.stream.close()
                self.pya.terminate()

            def save(self):
                with wave.open(self.audio.save_path, 'wb') as wavefile:
                    wavefile.setnchannels(self.channel)
                    wavefile.setsampwidth(self.pya.get_sample_size(self.format))
                    wavefile.setframerate(self.rate)
                    wavefile.writeframes(b"".join(self.play_frames))

        self.snd_record = SoundRecordPlay(maindlg=self)  
        self.snd_record_TD = QThread()
        self.snd_record.moveToThread(self.snd_record_TD) # 还是不太会用QThread
        self.snd_record.finished.connect(self.snd_record_TD.quit)
        self.snd_record_TD.started.connect(self.snd_record.record)
        #
        self.snd_play = SoundRecordPlay(maindlg=self)
        self.snd_play_TD = QThread()
        self.snd_play.moveToThread(self.snd_play_TD)
        self.snd_play.finished.connect(self.snd_play_TD.quit)
        self.snd_play_TD.started.connect(self.snd_play.play)
    
    def initTimer(self):
        self.lb_status_TM = QTimer() # 不一定要使用线程的计数方法（如果直接用while loop因为不是直接的qt调用，会锁死GUI）
        self.lb_status_dot_ctr = 0
        self.lb_status_TM_time_inv = 200 # QTimer的基本单位是毫秒
        num_inv = 10
        self.lb_status_TM.timeout.connect(lambda x=num_inv: self.refreshLBDot(x)) # 要传递参数就用lambda或from functools import partial partial(fun, para)
        self.lb_status_TM.timeout.connect(self.wave_spectrum_PG.updatePlot)
        
    def refreshLBDot(self, num_i):
        self.lb_status_dot_ctr += 1
        self.lb_status_dot_ctr %= num_i
        if self.is_snd_recording: # None时应该还不至于调集这个函数
            self.result_LB.setText("时长：{:.1f}秒，正在录音中{}".format(self.audio.record_duration
                                                                        ,"。"*self.lb_status_dot_ctr))
        else:
            self.result_LB.setText("时长：{:.1f}/{:.1f}秒，正在播放中{}".format(self.audio.play_duration, self.audio.record_duration
                                                                        ,"。"*self.lb_status_dot_ctr))
    
    def isRunning(self):
        self.lb_status_TM.start(self.lb_status_TM_time_inv)
    
    def notRunning(self):
        self.lb_status_TM.stop()
    
    def startRecord(self):
        self.snd_record.create()
        self.snd_record.start()
        self.audio.record_block_ctr = 0
        self.snd_record_TD.start()
        self.result_LB.setText("录音开始")
        self.record_BT.setText("暂停录音")
        self.isRunning()
        
    def pauseRecord(self):
        self.snd_record.pause()     
        self.result_LB.setText("录音暂停")
        self.record_BT.setText("继续录音")
        self.notRunning()
        
    def resumeRecord(self):
        self.snd_record.resume()
        self.result_LB.setText("录音恢复")
        self.record_BT.setText("暂停录音")
        self.isRunning()
    
    def stopRecord(self):
        self.snd_record.stop()
        self.result_LB.setText("录音停止")
        self.record_BT.setText("开始录音")
        self.notRunning()
    
    def resetRecord(self):
        self.snd_record_ctr = 0
        self.notRunning()
        self.result_LB.setText("欢迎使用")
        self.record_BT.setText("开始录音")
        self.reset_BT.setText("重来")
    
    def startPlay(self):
        self.snd_play.create()
        self.snd_play.start()
        self.audio.play_block_ctr = 0
        self.snd_play_TD.start()
        self.result_LB.setText("播放开始")
        self.play_BT.setText("暂停播放")#开始变成暂停
        self.isRunning()
        
    def pausePlay(self):
        self.snd_play.pause()
        self.result_LB.setText("播放暂停")
        self.play_BT.setText("继续播放")
        self.notRunning()

    def resumePlay(self):
        self.snd_play.resume()
        self.result_LB.setText("播放开始")
        self.play_BT.setText("暂停播放")
        self.isRunning()
    
    def stopPlay(self):
        self.snd_play.stop() # 预先设限
        if self.snd_play_TD.isFinished():
            pass
        else:
            if self.snd_play_ctr % 2 == 1:
                self.snd_play.pause()
            else:
                self.snd_play.resume() #帮助跳出while continue循环
            self.notRunning()
            
    def resetPlay(self):
        self.snd_play_ctr = 0
        self.play_BT.setText("开始播放")
        self.result_LB.setText("欢迎使用")
        self.reset_BT.setText("重来")
    
    def playFinished(self):
        self.result_LB.setText("播放结束")
        self.resetPlay()
        
    def click2Play(self):
        if self.snd_record_ctr == 0:
            pass
        elif self.snd_record_ctr % 2 == 1:
            self.pauseRecord()
            self.snd_record_ctr += 1 # 模拟一次点击，保持状态一致性
        else: 
            pass # self.pauseRecord()
        #
        self.is_snd_recording = False
        self.reset_BT.setText("停止播放")
        # 0 初始开始播放，<播放中> 1 可暂停播放 <播放停止中> 2 可继续播放 
        if self.snd_play_ctr == 0:
            self.startPlay()
        else:
            if self.snd_play_TD.isFinished():
                self.resetPlay()
            else:
                if self.snd_play_ctr % 2 == 1:
                    self.pausePlay()
                else:
                    self.resumePlay()
        self.snd_play_ctr += 1
        
    def click2Record(self):
        if self.snd_play_ctr == 0:
            pass
        else:
            self.stopPlay() 
            self.resetPlay()
        #
        self.is_snd_recording = True
        self.reset_BT.setText("停止录音")
        # 0 开始录音 <录音中> 1暂停 <>
        if self.snd_record_ctr == 0:
            self.startRecord()
        elif self.snd_record_ctr % 2 == 1:
            self.pauseRecord()
        else:
            self.resumeRecord()
        self.snd_record_ctr += 1

    def click2Reset(self):
        self.snd_reset_ctr += 1 # 纯属一些个人的恶趣味
        if self.is_snd_recording is None:
            if self.snd_reset_ctr == 1:
                self.result_LB.setText("请开始吧")
            elif self.snd_reset_ctr == 2:
                self.result_LB.setText("就是左边那两个按键呀")
            else:
                self.result_LB.setText("还不会呀，你个笨比")
        else:
            self.notRunning()
            if not self.is_snd_recording:
                self.stopPlay()
                self.resetPlay()
            else:
                self.stopRecord()
                self.resetRecord()

    def click2Save(self):
        self.lb_status_TM.stop()
        self.snd_record.pause()
        self.snd_record.save()
        self.result_LB.setText("录音保存在{}".format(self.audio.save_path))
    
  