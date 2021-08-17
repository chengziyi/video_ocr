import os
import shutil

def split_limit(sentence, output_filename, max_len=200):
    assert sentence is not None
    sentence = sentence.strip('\n')
    res = []
    def split(sen):
        if len(sen)>=max_len:
            res.append(sen[:max_len])
        else:
            res.append(sen)
            return
        split(sen[max_len:])

    split(sentence)

    with open(output_filename, 'w') as f:
        f.writelines('\n'.join(res))

def split_sentence_with_limit(sentence, output_filename, error_dir, split_ch='。', max_len=200):
    assert sentence is not None
    sentence = sentence.strip('\n')
    sen_list = sentence.split(split_ch)
    if '' in sen_list:
        sen_list.remove('')
    sen_list = list(map(lambda x:x+split_ch, sen_list))

    cur_len = 0
    cur_res = ''
    total_res = []
    for cur_sen in sen_list:
        cur_len += len(cur_sen)
        if cur_len <= max_len:
            cur_res += cur_sen
        else:
            total_res.append(cur_res)
            cur_res = cur_sen
            cur_len = len(cur_res)

    total_res.append(cur_res)

    length=0
    for i in total_res:
        length+=len(i)
    if length/len(total_res) > 200:
        print(f'file:{output_filename}, avg_len:{length/len(total_res)}')
        if not os.path.exists(error_dir):
            os.makedirs(error_dir)
        error_filename = output_filename.replace('splited_text','error_text')
        origin_filename = output_filename.replace('splited_text','original_text')
        shutil.copy(origin_filename, error_filename)

    with open(output_filename, 'w') as f:
        f.writelines('\n'.join(total_res))

if __name__ == "__main__":
    ##有句号的按句号分, 没有句号按逗号分, 逗号都没有的直接按200字分
    input_dir = './original_text'
    output_dir = './splited_text'
    error_dir = './error_text'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for input_file in os.listdir(input_dir):
        input_file_path = os.path.join(input_dir, input_file)
        data=None
        with open(input_file_path, "r") as f:
            data = f.read()

        output_path = os.path.join(output_dir, input_file)
        split_sentence_with_limit(data, output_path, error_dir, split_ch='，')

    # input_dir = './error_text'
    # output_dir = './splited_text'
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    # for input_file in os.listdir(input_dir):
    #     input_file_path = os.path.join(input_dir, input_file)
    #     data=None
    #     with open(input_file_path, "r") as f:
    #         data = f.read()
    #     output_path = os.path.join(output_dir, input_file)
    #     split_limit(data, output_path)

