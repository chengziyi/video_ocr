import requests
import os
import cv2
import base64
import time
import shutil
import argparse

def timmer(func):
    def deco(*args, **kwargs):
        print('\nfunction: {_funcname_} start:'.format(_funcname_=func.__name__))
        start_time = time.time()
        res = func(*args, **kwargs)
        end_time = time.time()
        print('function:{_funcname_} use {_time_} sec'
              .format(_funcname_=func.__name__, _time_=(end_time - start_time)))
        return res
    return deco

class Ocr(object):
    def __init__(self):
        self.url = 'http://10.8.1.6:10124/api/tr-run/'
        # self.url = 'http://172.17.0.3:10124/api/tr-run/'

    def pick_chinese(self, check_str):
        res_str=''
        for ch in check_str:
            if u'\u4e00' <= ch <= u'\u9fef' or ch in ['，','。','、','“','”','：'] or '0'<=ch<='9' or 'a'<=ch<='z' or 'A'<=ch<='Z':
                res_str += ch
        return res_str

    def check_contain_chinese(self, check_str):
        for ch in check_str:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False

    def Request_file(self, url,img_file):
        response= requests.post(url=url, data={'compress': 0}, files=img_file)
        response.encoding = 'utf-8'
        if response.ok:
            data = response.json()['data']['raw_out']
        else:
            print('request return not ok, ',response.status_code)
        return data

    def test_ocr(self):
        def img_to_base64(img_path):
            with open(img_path, 'rb')as read:
                b64 = base64.b64encode(read.read())
            return b64

        img_b64 = img_to_base64('./testimg.png')
        res = requests.post(url=self.url, data={'img': img_b64})
        res.encoding = 'utf-8'
        if res.ok:
            data = res.json()['data']['raw_out']
        else:
            print('request return not ok, ',res.status_code)
            return
        print(data)

    def lcs(self, ocr_str, text_str):
        ## input two str
        max_length = 0
        max_last_index = 0
        dp = [[0]*(len(text_str)+1) for i in range(len(ocr_str)+1)]
        for i in range(len(ocr_str)):
            for j in range(len(text_str)):
                if ocr_str[i] == text_str[j]:
                    dp[i+1][j+1] = dp[i][j]+1
                    if dp[i+1][j+1] >= max_length:
                        max_length = dp[i+1][j+1]
                        max_last_index = i

        if max_length != 0:
            sub_str = ocr_str[max_last_index-max_length+1:max_last_index+1]
        else:
            sub_str = ''
        print(ocr_str)
        print(text_str)
        return sub_str, max_length

    def request_img(self, img_data):
        img_b64 = base64.b64encode(img_data)
        data = {'img': img_b64}
        response = requests.post(url=self.url, data=data)
        response.encoding = 'utf-8'
        if response.ok:
            res = response.json()['data']['raw_out']
        else:
            res = None
            print('request return not ok, ',response.status_code)
        return res

    def data_filter(self, data_list):
        keep_data_list = []
        for data_i in data_list:
            if data_i[1] != '' and data_i[2] >= 0.99:
                keep_data_list.append(data_i)

        if len(keep_data_list) > 1:
            print("WARN: ocr result more than 1, combine")
            data_str_list = []
            for i in keep_data_list:
                data_str_list.append(i[1])

            data_str = ''.join(data_str_list)
            data_str2 = ''
            for ch in data_str:
                if not 'a'<=ch<='z':
                    data_str2+=ch
            combine_data = [[0,0,0], data_str2, 1.0]
            keep_data_list.insert(0, combine_data)
            print(keep_data_list)
        elif len(keep_data_list) == 0:
            print("can not get any ocr in this frame")
            return None

        return [keep_data_list[0]]

    @timmer
    def run(self, input_video, input_txt, output_text, error_path=None):
        ## read text
        with open(input_txt, 'r') as f:
            text_data = f.readlines()
        text_data_iter = iter(text_data)
        ori_data_len = len(text_data)
        #读取视频
        cap = cv2.VideoCapture(input_video)
        #获取视频帧率
        fps_video = round(cap.get(cv2.CAP_PROP_FPS))
        #获取视频宽度
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        #获取视频高度
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_time = round(total_frames/fps_video)
        print(cap,f"fps:{fps_video}, w:{frame_width}, h:{frame_height}, frames:{total_frames}, time:{total_time}")

        ocr_text_list = []
        frame_id = 0
        time_last = 0

        try:
            cur_text = next(text_data_iter)
            if cur_text == '\n':
                cur_text = next(text_data_iter)
        except StopIteration:
            print('ERROR:Can not get text data...')
            return None

        cur_result = cur_text
        final_result = []
        ## 每秒一次,截取字幕区域,ocr识别,检查ocr结果是否非空且包含中文且置信度>0.99,多帧ocr去重
        ## 和当前字幕段落匹配, 检查ocr结果是否包含在字幕段落中(需要允许个别错误),找到起始位置和最终位置
        ## 如果起始位置在字幕段落开头,记录当前时间, 如果最终位置在字幕段落结尾,读取下一段字幕
        ## 每次匹配到字幕段落开头就将当前时间和上次记录的时间间隔作为上一段字幕段落的持续时间,所以要处理最后一段
        ## 注意:基于文本连续性假设,即相邻两段文本之间不会有较长的间隔,否则会出现字幕已经结束而朗读还在继续的情况
        while(cap.isOpened()):
            ret, frame = cap.read()
            if ret is not True:
                break
            if ret == True:
                frame_id += 1
                ## 每秒一次
                if frame_id % fps_video == 0:
                    cur_time = frame_id/fps_video
                    if cur_time%10==0:
                        print(f"frame:{frame_id}, time(sec):{cur_time}")

                    ## 截取字幕区域,ocr识别
                    frame = frame[595:690, :]
                    # cv2.imwrite('tmp.jpg',frame)
                    img_str = cv2.imencode('.png', frame)[1].tobytes()
                    data = self.request_img(img_str)
                    if len(data) > 1:
                        ## in this case,ocr must be only one
                        data = self.data_filter(data)
                        if data is None:
                            continue
                    for i in range(len(data)):
                        ocr_text = data[i][1]
                        ocr_text = self.pick_chinese(ocr_text)
                        if ocr_text !='' and self.check_contain_chinese(ocr_text):
                            ## ocr去重
                            if ocr_text not in ocr_text_list:
                                ocr_text_list.append(ocr_text)

                                ## 检查ocr结果是否包含在字幕段落中,求最长公共子串
                                ## 如果LCS存在且长度大于阈值则认为ocr结果是正确的,否则说明ocr识别了错误的内容
                                ## 如果ocr识别了错误的内容, 丢弃
                                common_str, lcs_length = self.lcs(ocr_text, cur_text)
                                if lcs_length==0:
                                    print(f'check ocr result:\n',f'ocr:{ocr_text}\n',
                                        f'text:{cur_text}')
                                else:
                                    ## 判断公共子串处于字幕段落的开头还是结尾
                                    ## 注意:最长公共子串有可能不是刚好位于开头或结尾
                                    str_start = cur_text.find(common_str)
                                    str_end = str_start + len(common_str)
                                    print(f'debug: {common_str} {str_start}')
                                    if str_start <= 5:
                                        time_start = cur_time
                                        if time_last <= time_start:
                                            if time_last != 0:
                                                dura_str = f"{time_last}-{time_start}"
                                                cur_result = '\t'.join([cur_result.strip('\n'), dura_str])
                                                final_result.append(cur_result + '\n')
                                                cur_result = cur_text
                                            time_last = time_start

                                    ## 字幕段落结尾
                                    if str_end == len(cur_text.strip('。\n')):
                                        try:
                                            cur_text = next(text_data_iter)
                                            if cur_text == '\n':
                                                cur_text = next(text_data_iter)
                                        except StopIteration:
                                            print('no more text data')
                                            print(f'cur_result:{cur_result}, time_last:{time_last}')
                                            dura_str = f"{time_last}-{total_time}"
                                            cur_result = '\t'.join([cur_result.strip('\n'), dura_str])
                                            final_result.append(cur_result + '\n')

        with open(result_path, 'w') as f:
            f.writelines(final_result)

        result_data_len = len(final_result)
        if result_data_len != ori_data_len:
            print("check result: ", result_path)
            if error_path is not None:
                shutil.copy(result_path, error_path)

if __name__=='__main__':
    error_result_dir = './error_result'
    output_dir = './output'
    assert os.path.exists(error_result_dir)
    assert os.path.exists(output_dir)

    parser = argparse.ArgumentParser()
    parser.add_argument('--video_dir',default=None)
    video_dir = parser.parse_args().video_dir
    assert video_dir is not None
    print(video_dir)
    for video_name in os.listdir(video_dir):
        if video_name[-4:] == '.mp4':
            video_path = os.path.join(video_dir, video_name)
            txt_name = video_name.replace('.mp4', '.txt')
            input_txt = os.path.join(video_dir, txt_name)
            result_path = os.path.join(output_dir, 'res_'+txt_name)
            print(video_name)
            print(txt_name)
            error_path = os.path.join(error_result_dir, txt_name)
            Ocr().run(video_path, input_txt, result_path, error_path)
