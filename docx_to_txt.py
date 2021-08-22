from docx import Document
import os

def doc_to_txt(file_path):
    data=[]
    f = open(file_path, 'rb')

    text_list=[]
    doc=Document(f)
    for i in doc.paragraphs:
        text_list.append(i.text)

    f.close()
    if '' in text_list:
        text_list.remove('')
    # print(text_list)
    txt_file_path = file_path.replace('.docx', '.txt')
    with open(txt_file_path, 'w') as f:
        f.writelines(text_list)

def split_sentence_with_limit(input_filename, output_filename, split_ch='。', max_len=100):
    assert input_filename is not None

    with open(input_filename, 'r') as f:
        sentence = f.readlines()

    assert len(sentence)==1
    sentence=sentence[0]
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
    # print(total_res)
    total_res = '\n'.join(total_res)
    with open(output_filename, 'w') as f:
        f.writelines(total_res)

if __name__ == '__main__':
    ## doc to txt
    for file_path in ['./tmp/风景视频11.docx', './tmp/风景视频12.docx']:
        doc_to_txt(file_path)

        ## split txt
        txt_path=file_path.replace('.docx', '.txt')
        txt_output=txt_path.replace('.txt', '_splited.txt')
        split_sentence_with_limit(txt_path, txt_output)
