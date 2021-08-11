import os

data=None
with open("1.txt", "r") as f:
    data = f.read()

def split_sentence_with_limit(sentence, split_ch='。', max_len=200):
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

    with open('split_result.txt', 'w') as f:
        f.writelines('\n'.join(total_res))

if __name__ == "__main__":
    split_sentence_with_limit(data)
