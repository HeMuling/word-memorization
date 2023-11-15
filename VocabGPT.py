# if you wish to use this preset (i.e. prompt)
# you can find it here: https://platform.openai.com/playground/p/TLhnV8qhi4waAl9MyYvdMUZQ?model=gpt-4-1106-preview&mode=chat

from openai import OpenAI
import pandas as pd
import os

def break_input(input_message:str)->list:
    vocab_token = input_message.split("--")[0]
    type_token = input_message.split("--")[-1] if len(input_message.split("--")) == 2 else "exp"

    return [vocab_token, type_token]

def response_from_gpt(input_message:str)->list:
    '''
    args:
        input_message: str, input message from user
    return:
        response: list, [vocab_token, type_token, output]

    get message from user, send to GPT-4, and return the response
    '''
    vocab_token, type_token = break_input(input_message)
    
    client = OpenAI()
    response = client.chat.completions.create(
    model="gpt-4-1106-preview",
    messages=[
        {
        "role": "system",
        "content": '''扮演一位英语母语者，你的任务是帮我记忆英语单词，准备GRE与雅思的考试。\n
                        我会输入一个英语单词，并给你一个任务名称。格式为\"[英语单词]--[任务名称]\"\n
                        \n
                        当任务名称为\"exp\"时：你需要做的是用英文分点列出单词的含义，这些含义应该来自柯林斯字典等权威书籍与字典，
                        对于每一个含义，给1-2个英语句子，句子需要满足写作规范，按照GRE与雅思的写作，并给出中文翻译。\n
                        \n
                        当任务名称为\"mem\"时：你需要帮助我对单词进行记忆。执行这个任务时需要你完成3件事：1. 根据词根分解单词，
                        并给出单词。2.给出单词的派生 3. 给出单词的来源，可以是历史上的来源，也可以是给出是从哪个词衍生来的。\n
                        \n
                        如果没有指定任务，则默认任务为\"exp\"\n
                        \n
                        \"exp\"范例：\n
                        The word \"suppliant\" is often associated with a sense of deep humility, earnestness,
                        and a position of lesser power relative to the person being addressed. It is both a 
                        reflection of the demeanor of the person requesting and the nature of the petition being made.\n
                        1. **Meaning as an adjective**: Humbly pleading or beseeching.\n
                            - Sentence: The suppliant tone of the petitioner moved the council to consider the appeal.\n
                            - Chinese: 恳求者的恳切语气感动了委员会去考虑这项上诉。\n
                        2. **Meaning as a noun**: A person making a humble plea to someone in power or authority.\n
                            - Sentence: The king faced a group of suppliants begging for clemency outside the palace gates.\n
                            - Chinese: 国王面对一群在宫殿大门外乞求宽恕的恳求者。\n
                        \n
                        \"mem\"范例：\n
                        1. **词根分解**：\"exotic\" 的词源可以追溯到希腊语的 \"exotikos,\" 表示 \"来自外部的\"。\"Exo\" 是一个希腊语前缀，意为 \"外面\"。\n
                        2. **派生词**： 从 \"exotic\" 派生出来的词有 \"exotica\" （指异国风情的事物集合），\"exoticism\" （对异国文化特征的迷恋或模仿）。\n
                        3. **词源**： \"exotic\" 来自希腊语 \"exotikos\"，这进一步源自 \"exo\"（外面）。这个词首先是形容词 \"exo\" 的派生，意为 \"来自远方的\"
                        或 \"非本地的\"，延伸出我们今天所理解的 \"具有异国特色\" 或 \"外来稀奇\" 的含义。\n
                        \n
                        回答不要太长，要简洁、精炼。格式按照\"exp\"书写。
        },'''
        },
        {
        "role": "user", "content": input_message
        }
    ],
    temperature=1,
    max_tokens=4095,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    output = response.choices[0].message.content

    return [vocab_token, type_token, output]

def cache_response(response:list):
    '''
    args:
        response: list, [vocab_token, type_token, output]
    return:
        None

    cache the response from GPT-4:
    first check wheather the cache file exists, if not, create one
    the cache file is a .csv and has 3 columns: vocabab, exp, mem
    then store the response into the cache file for further use
    '''
    vocab_token, type_token, output = response
    if os.path.exists("vocab.csv"):
        cache = pd.read_csv("vocab.csv", encoding='utf-8')
        if vocab_token in cache['vocab'].values:
            cache.loc[cache['vocab'] == vocab_token, type_token] = output
        else:
            new_row = pd.DataFrame({"vocab": [vocab_token], "exp": [''],"mem": ['']})
            new_row[type_token] = output
            cache = pd.concat([cache, new_row], ignore_index=True)
    else:
        cache = pd.DataFrame({"vocab":vocab_token, "exp": output if type_token=='exp' else '', "mem": output if type_token=='mem' else ''}, index=[0])
    cache.to_csv("vocab.csv", index=False, encoding='utf-8')

def read_cache(input_message:str)->list:
    '''
    args:
        input_message: str, input message from user
    return:
        response: list, [vocab_token, type_token, output] or [vocab_token, type_token, ''] depending on wheather the vocabulary is in cache file
    
    read cache file if exists
    then, check if the vocabulary user queried is in the cache file
    if yes, return the response from cache file
    if no, return an empty string
    '''
    vocab_token, type_token = break_input(input_message)
    if os.path.exists("vocab.csv"):
        cache = pd.read_csv("vocab.csv", encoding='utf-8')
    else:
        return [vocab_token, type_token, '']
    if vocab_token in cache['vocab'].values and str(cache.loc[cache['vocab'] == vocab_token, type_token].values[0])!='nan':
        output = cache.loc[cache['vocab'] == vocab_token, type_token].values[0]
        return [vocab_token, type_token, output]
    else:
        return [vocab_token, type_token, '']
    
def main():
    '''
    continue to ask user for input until user input '!quit'
    '''
    continue_token = True
    while continue_token:
        input_message = input("请输入查询单词，格式为\"[英语单词]--[任务名称]\"：")
        if input_message == '!quit':
            continue_token = False
            break
        else:
            vocab_token, type_token, output = read_cache(input_message)
            if output == '':
                response = response_from_gpt(input_message)
                cache_response(response)
                print(response[-1])
            else:
                print(output)

if __name__ == "__main__":
    main()