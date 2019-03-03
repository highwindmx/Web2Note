import os
import numpy as np
from PyQt5.QtCore import (Qt, QUrl, QFile, QBuffer, QByteArray, QIODevice, QObject, QThread, QTimer, pyqtSignal, pyqtSlot)# 
from PyQt5.QtGui import (QIcon, QPixmap, QImage)
from PyQt5.QtWidgets import (QDialog, QFileDialog, QWidget, QListWidget, QListWidgetItem
                            ,QGridLayout, QSizePolicy, QSlider, QLabel, QPushButton)
from PyQt5.QtMultimedia import (QAudioOutput, QAudioInput, QAudio, QMultimedia, QAudioFormat
                               ,QAudioDeviceInfo, QAudioProbe, QMediaPlayer, QMediaContent)
import pyqtgraph as pg
import wave
import scipy.io.wavfile as scwav
from python_speech_features import mfcc
import librosa
# 没办法scipy.talkbox那个库总是安装失败。。。
from dtw import dtw
from numpy.linalg import norm as nlnorm

class Audio:
    def __init__(self, chunksize=512, rate=44100, channel=2, sample_size=8
                ,codec="audio/pcm", threshold=500, save_dir=None):
        self.chunksize = chunksize
        self.rate = rate
        self.sample_size = sample_size
        self.channel = channel
        self.sampleWidth = 2
        #
        self.format = QAudioFormat()
        self.format.setChannelCount(self.channel)
        self.format.setSampleRate(self.rate)
        self.format.setSampleSize(self.sample_size)
        self.format.setCodec(codec)
        self.format.setByteOrder(QAudioFormat.LittleEndian) # 1
        self.format.setSampleType(QAudioFormat.UnSignedInt) # 2 这个应该就决定了录音的质量，不然会有很强的滋滋声音
        #
        self.block = b"" # bytes 类型
        self.record_buffer = QBuffer()
        self.play_buffer = QBuffer()  
        # 不能用QIODevice()，因为这是个c++的虚类(还没有python实体化？), 
        # 顺便也就不用所谓的QAudioBuffer类了
        #
        self.pos = 0
        self.duration = 0
        #self.play_block_ctr = 0
        #self.play_duration = 0
        #
        self.threshold = threshold
        self.save_dir = save_dir
        self.save_path = "./sound/test.wav"
        
    def saveWave(self):
        with wave.open(self.save_path, 'wb') as wf:
            wf.setnchannels(self.channel)
            wf.setsampwidth(self.sampleWidth)
            wf.setframerate(self.rate)
            wf.writeframes(self.record_buffer.data())
    
               
class AudioAnalysis(QDialog):
    #recordFinished = pyqtSignal()
    #playFinished = pyqtSignal()
    #
    def __init__(self, mainwin, dir):
        super().__init__()
        #self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.main_Win = mainwin
        self.snd_record_ctr = 0 
        self.snd_play_ctr = 0
        self.snd_reset_ctr = 0
        self.is_snd_recording = None
        #
        self.audio = Audio(save_dir=dir)
        self.initAUD()
        self.initIF()
        self.initWaveList()

    def initIF(self):
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        icon = QIcon()
        icon.addPixmap(QPixmap("./style/logo3.png"))
        self.setWindowIcon(icon)
        self.setWindowTitle("语音录制与分析")
        self.list_LW = QListWidget(self)
        self.list_LW.setMaximumWidth(160)
        class WaveSpectrum(QWidget):
            def __init__(self, parent=None, maindlg=None):
                super(WaveSpectrum, self).__init__(parent)
                self.main_Dlg = maindlg
                #self.pg_PL = pg.PlotWidget(enableMenu=False)
                self.audio = self.main_Dlg.audio
                self.layout = QGridLayout(self)
                self.setLayout(self.layout)
                self.pg_PL = pg.PlotWidget() #pg.plot(title="Three plot curves")
                self.pg_PL.hideButtons()
                self.layout.addWidget(self.pg_PL)
                
                self.item = self.pg_PL.getPlotItem()
                self.item.hideButtons()
                self.item.setMouseEnabled(y=False)
                self.item.setYRange(0,20000)
                range = self.audio.rate/2
                self.item.setXRange(-range,range, padding=0)
                self.axis = self.item.getAxis("bottom")
                self.axis.setLabel("频率（赫兹）")
                
            def updatePlot(self):
               try:
                   data = np.fromstring(self.audio.block, 'int16')
                   #print(data)
                   T = 1.0/self.audio.rate
                   N = data.shape[0]
                   Fx = (1./N) * np.fft.fft(data) # 万一N==0
               except Exception as e:
                   print("??",e)
               else:
                   f = np.fft.fftfreq(N, T)
                   Fx = np.fft.fftshift(Fx)
                   f = np.fft.fftshift(f)
                   self.item.plot(x=f.tolist(), y=(np.absolute(Fx)).tolist(), clear=True)    
    
        self.wave_spectrum_PG = WaveSpectrum(maindlg=self)
        self.result_LB = QLabel(self)
        self.result_LB.setText("欢迎使用")
        self.running_SL = QSlider(Qt.Horizontal)
        self.running_SL.setMinimum(0)
        self.running_SL.setMaximum(100)
        self.running_SL.setStyleSheet("QSlider::handle:horizontal {background-color: #d91900;}")
        self.save_BT = QPushButton(self)
        self.save_BT.setText("保存与分析")
        self.save_BT.setMinimumSize(128,32)
        self.record_BT = QPushButton(self)
        self.record_BT.setText("开始录音")
        self.record_BT.setMinimumSize(144,32)
        self.play_BT = QPushButton(self)
        self.play_BT.setText("开始播放")
        self.play_BT.setMinimumSize(144,32)
        self.reset_BT = QPushButton(self)
        self.reset_BT.setText("停止")
        self.reset_BT.setMinimumSize(128,32)
               
        self.layout.addWidget(self.list_LW, 0,0,1,1)
        self.layout.addWidget(self.wave_spectrum_PG, 0,1, 1,3)
        self.layout.addWidget(self.result_LB, 1,0, 1,4)
        self.layout.addWidget(self.running_SL, 2,0, 1,4)
        self.layout.addWidget(self.save_BT, 3,0, 2,1)
        self.layout.addWidget(self.record_BT, 3,1, 2,1)
        self.layout.addWidget(self.play_BT, 3,2, 2,1)
        self.layout.addWidget(self.reset_BT, 3,3, 2,1)
        

        self.list_LW.itemClicked.connect(self.sel2Play)
        self.record_BT.clicked.connect(self.click2Record)
        self.running_SL.sliderReleased.connect(self.dragPosPlay) 
        # 注意这里得是用户主动的动作哟 另外如果需要点击位置定位的话还必须要重写mousePressEvent，这里就不弄了
        self.play_BT.clicked.connect(self.click2Play)
        self.reset_BT.clicked.connect(self.click2Reset)
        self.save_BT.clicked.connect(self.click2Save)
    
    def initWaveList(self):
        self.wave_dict = {"小黄":["catH1.wav",0],"小黄骚":["catH2.wav",0], "小黄又骚":["catH3.wav",0], "小黄又又骚":["catH4.wav",0]
                         ,"煤球":["catM1.wav",0],"煤球骚":["catM2.wav",0], "煤球又骚":["catM3.wav",0]
                         ,"老公":["laog.wav",0], "老婆":["laop.wav",0]}
        
        for k in self.wave_dict:
            item = QListWidgetItem()
            item.setText(k)
            item.setData(Qt.UserRole, self.wave_dict[k])
            self.list_LW.addItem(item)
            
    def initAUD(self):
        #
        info = QAudioDeviceInfo.defaultInputDevice()
        if (~info.isFormatSupported(self.audio.format)):
            # print("警告，设置的默认音频格式并不支持，将尝试采用最相近的支持格式")
            # 不知道这里面有什么神改动？
            self.audio.format  = info.nearestFormat(self.audio.format)
        #
        update_interval = 160
        self.audioRecorder = QAudioInput(self.audio.format)
        self.audioRecorder.setNotifyInterval(update_interval) #按毫秒ms 类似于QTimer的作用
        self.audioRecorder.notify.connect(self.processAudioData)
        self.audioRecorder_TD = QThread()
        self.audioRecorder.moveToThread(self.audioRecorder_TD)
        self.audioRecorder_TD.started.connect(self.startRecord)
        self.audioRecorder.stateChanged.connect(self.recordStopped)
        #
        self.audioPlayer = QAudioOutput(self.audio.format)
        self.audioPlayer.setNotifyInterval(update_interval)
        self.audioPlayer.notify.connect(self.processAudioData)
        self.audioPlayer_TD = QThread()
        self.audioPlayer.moveToThread(self.audioPlayer_TD)
        self.audioPlayer_TD.started.connect(self.startPlay)
        self.audioPlayer.stateChanged.connect(self.playStopped)
    
    #   
    def startRecord(self):
        self.audioRecorder.start(self.audio.record_buffer) # 独立出来主要就是为了传个参数进去
        
    def click2Record(self):
        if self.snd_play_ctr != 0:
            self.audioPlayer.suspend()
            self.audioPlayer.stop()
            self.audio.play_buffer.close()
            self.running_SL.setValue(0)
            self.audioPlayer_TD.quit()
            self.snd_play_ctr = 0
            self.play_BT.setText("开始播放")
        #
        self.is_snd_recording = True
        self.running_SL.setStyleSheet("QSlider::handle:horizontal {background-color: #d91900;}")
        self.running_SL.setValue(0)
        if self.snd_record_ctr == 0:
            self.audio.record_buffer.open(QIODevice.WriteOnly)
            self.audioRecorder_TD.start() #注意这里是分线程进行
            self.record_BT.setText("暂停录音")
            self.reset_BT.setText("停止录音")
        elif self.snd_record_ctr % 2 == 1:
            self.audioRecorder.suspend()
            self.result_LB.setText("录音暂停")
            self.record_BT.setText("继续录音")
        else: # self.snd_record_ctr % 2 == 0:
            self.audioRecorder.resume()
            self.record_BT.setText("暂停录音")
        self.snd_record_ctr += 1

    def recordStopped(self):
        if self.audioRecorder.state() == QAudio.StoppedState: #==2 #QAudio.IdleState: #==3;
            self.audioRecorder_TD.quit()

    def startPlay(self):
        self.audioPlayer.start(self.audio.play_buffer)

    def click2Play(self):
        if self.is_snd_recording == None:
            self.result_LB.setText("还没录音呢！！！")
        else:
            if self.snd_record_ctr % 2 == 1:
                self.audioRecorder.suspend()
                self.record_BT.setText("继续录音")
                self.snd_record_ctr += 1
            #
            self.is_snd_recording = False
            self.running_SL.setStyleSheet("QSlider::handle:horizontal {background-color: #007ad9;}")
            if self.snd_play_ctr == 0:
                data = self.audio.record_buffer.data()      
                self.audio.play_buffer.setData(data)
                self.audio.play_buffer.open(QIODevice.ReadOnly) # 要在关闭的情况下设置数据然后在以某种模式打开
                self.audioPlayer_TD.start()
                self.running_SL.setValue(0)
                self.start_time = 0
                # self.start_time = self.running_SL.value() / 100 * self.audio.duration
                # self.audioPlayer.setVolume(0.8)
                self.play_BT.setText("暂停播放")
                self.reset_BT.setText("停止播放")
            elif self.snd_play_ctr % 2 == 1:
                self.audioPlayer.suspend()
                self.result_LB.setText("播放暂停")
                self.play_BT.setText("继续播放")
            else:    
                self.audioPlayer.resume()
                self.play_BT.setText("暂停播放")
            self.snd_play_ctr += 1
    
    def playStopped(self):
        if self.audioPlayer.state() == QAudio.IdleState: #==3; #QAudio.StoppedState: #==2
            self.audioPlayer.stop()
            self.running_SL.setValue(0)
            self.audio.play_buffer.close()
            self.audioPlayer_TD.quit()
            self.snd_play_ctr = 0
            self.play_BT.setText("开始播放")
    
    def dragPosPlay(self):
        if self.is_snd_recording == None:
            self.running_SL.setValue(0)
        else:
            if self.is_snd_recording & (self.snd_record_ctr % 2 == 1):
                self.audioRecorder.suspend()
                self.record_BT.setText("继续录音")
                self.snd_record_ctr += 1
            if (not self.is_snd_recording) & (self.snd_play_ctr % 2 == 1):
                self.audioPlayer.suspend()
                self.play_BT.setText("继续播放")
                self.snd_play_ctr += 1
            self.is_snd_recording = False
            self.running_SL.setStyleSheet("QSlider::handle:horizontal {background-color: #007ad9;}")
            self.audioPlayer.stop()
            self.audio.play_buffer.close()
            self.audioPlayer_TD.quit()
            #
            data = self.audio.record_buffer.data()      
            self.audio.play_buffer.setData(data)
            self.audio.play_buffer.open(QIODevice.ReadOnly) # 要在关闭的情况下设置数据然后在以某种模式打开
            self.audioPlayer_TD.start()
            data_size = self.audio.record_buffer.data().size()
            sel_pcent = self.running_SL.value() / 100
            sel_size = int(sel_pcent * data_size)
            self.audio.pos = int(sel_pcent * (data_size / self.audio.chunksize)) # 重设第几个chunk开始播放
            self.start_time = int(sel_pcent * self.audio.duration) # 重设开始播放时间
            self.audio.play_buffer.seek(sel_size)
            self.snd_play_ctr = 1
            self.play_BT.setText("暂停播放")
    
    def sel2Play(self, item):
        c0 = (self.is_snd_recording == None)
        c1 = ((self.is_snd_recording == False) & (self.snd_play_ctr % 2 == 0))
        c2 = ((self.is_snd_recording == True) & (self.snd_record_ctr % 2 == 0))
        if (c0 | c1 | c2):
            self.cur_item = item
            sound_dir = "./sound/"
            #self.cur_wave = os.path.abspath(item.data(Qt.UserRole)[0])
            self.cur_wave = item.data(Qt.UserRole)[0]
            sound_path = os.path.join(sound_dir, self.cur_wave)
            with wave.open(sound_path, 'rb') as wf:
                data = wf.readframes(wf.getnframes())
                self.audio.play_buffer.setData(data)
                self.audio.play_buffer.open(QIODevice.ReadOnly)
                self.start_time = 0
                self.audio.duration = 10 # 随便给了个值，避免产生除0的问题其他没啥用
                self.audioPlayer_TD.start()           
    
    def click2Reset(self):
        if self.is_snd_recording == None:
            self.result_LB.setText("还没录音呢！！！")
        elif self.is_snd_recording:
            self.audioRecorder.stop()
            self.audio.record_buffer = QBuffer()
            self.snd_record_ctr = 0
            self.result_LB.setText("录音停止")
            self.record_BT.setText("开始录音")
        else: #not self.is_snd_recording:
            self.audioPlayer.stop()
            self.audio.pos = 0
            self.snd_play_ctr = 0
            self.result_LB.setText("播放停止")
            self.play_BT.setText("开始播放")
        self.running_SL.setValue(0)
        
    def click2Save(self):
        if self.is_snd_recording == None:
            self.result_LB.setText("还没录音呢！！！")
        elif self.is_snd_recording:
            self.audioRecorder.suspend()
        else:
            self.audioPlayer.suspend()
        #self.audio.save_path = QFileDialog().getSaveFileName(self.main_Dlg, "选个保存的地方吧", new_path)[0]
        # 注意末尾那个[0]别丢了，不然返回的是tuple类型
        self.audio.saveWave()
        self.snd_record_ctr = 0
        self.result_LB.setText("录音存于：{}；刚刚应该是{}叫了:)".format(os.path.abspath(self.audio.save_path), self.getMinDist()))
        self.record_BT.setText("开始录音")
         
    def processAudioData(self):
        if self.is_snd_recording: #self.audioRecorder.state() == QAudio.ActiveState:
            self.audio.block = self.audio.record_buffer.data().right(self.audio.chunksize)
            self.audio.duration = self.audioRecorder.processedUSecs() # 注意这里是微秒！！！
            interval = 10
            self.running_SL.setValue((self.audio.duration / 1000000) % interval * (100 / interval))
            show_info = "已录制{:.1f}秒".format(self.audio.duration/1000000.0)
            self.result_LB.setText(show_info)
        else: # self.audioPlayer.state() == QAudio.ActiveState:
            # 试过chop 不过好像没有必要
            self.audio.block = self.audio.play_buffer.data().mid(self.audio.pos*self.audio.chunksize, self.audio.chunksize)
            self.audio.pos += 1
            self.running_SL.setValue((self.start_time + self.audioPlayer.processedUSecs())/self.audio.duration*100)
            show_info = "正在播放{:.1f}/{:.1f}秒".format((self.start_time + self.audioPlayer.processedUSecs())/1000000.0
                                                         ,self.audio.duration/1000000.0)
            self.result_LB.setText(show_info)
        self.wave_spectrum_PG.updatePlot()

    def getMFCC(self,path):
        (rate, sig) = scwav.read(path)
        mfcc_feature = mfcc(sig, rate)
        #print(mfcc_feature)
        nmfcc = np.array(mfcc_feature)
        #print(nmfcc)
        # return nmfcc
        y, sr = librosa.load(path)
        return librosa.feature.mfcc(y, sr)
        
    def compareMFCC(self, demo_path):
        mfcc1 = self.getMFCC(self.audio.save_path)
        print(demo_path)
        mfcc2 = self.getMFCC(demo_path)
        norm = lambda x, y: nlnorm(x-y, ord=1)
        d, cost_matrix, acc_cost_matrix, path = dtw(mfcc1.T, mfcc2.T, dist=norm)
        #print(d)
        return d
       
    def getMinDist(self):
        i = 1000000
        sound_dir = "./sound/"
        for k in self.wave_dict:
            self.wave_dict[k][1] = self.compareMFCC(os.path.join(sound_dir, self.wave_dict[k][0]))
            print("{}：{:.1f}".format(k, self.wave_dict[k][1]))
            i = min(i, self.wave_dict[k][1])
            if i == self.wave_dict[k][1]:
                min_k = k
        return min_k
    
  