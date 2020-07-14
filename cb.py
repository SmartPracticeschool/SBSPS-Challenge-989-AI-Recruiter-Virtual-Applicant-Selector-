import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

from cloudant.client import Cloudant 
import numpy
import tflearn
import tensorflow
import random
import json
import pickle

client = Cloudant.iam(username, apikey) 
client.connect()
dbI = client['interview_que']

tensorflow.compat.v1.disable_eager_execution()

with open("intents.json") as file:
    data = json.load(file)

try:
    with open("data.pickle", "rb") as f:
        words, labels, training, output = pickle.load(f)
except:
    words = []
    labels = []
    docs_x = []
    docs_y = []

    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            wrds = nltk.word_tokenize(pattern)
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent["tag"])

        if intent["tag"] not in labels:
            labels.append(intent["tag"])

    words = [stemmer.stem(w.lower()) for w in words if w != "?"]
    words = sorted(list(set(words)))

    labels = sorted(labels)

    training = []
    output = []

    out_empty = [0 for _ in range(len(labels))]

    for x, doc in enumerate(docs_x):
        bag = []

        wrds = [stemmer.stem(w.lower()) for w in doc]

        for w in words:
            if w in wrds:
                bag.append(1)
            else:
                bag.append(0)

        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1

        training.append(bag)
        output.append(output_row)


    training = numpy.array(training)
    output = numpy.array(output)

    with open("data.pickle", "wb") as f:
        pickle.dump((words, labels, training, output), f)

tensorflow.compat.v1.reset_default_graph()

net = tflearn.input_data(shape=[None, len(training[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(output[0]), activation="softmax")
net = tflearn.regression(net)

model = tflearn.DNN(net)

try:
    model.load("model.tflearn")
except:
    model.fit(training, output, n_epoch=1000, batch_size=8, show_metric=True)
    model.save("model.tflearn")


def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1
            
    return numpy.array(bag)


namesList = ['aditi', 'aadesh', 'adesh', 'akash', 'aakash', 'akaash', 'aarav', 'arav', 'abhay', 'abhimanyu', 'abhinav', 'adit', 'ajay', 'akshaj', 'akshant', 'akshat', 'akshay', 'amandeep', 'aniket', 'ankit', 'ansh', 'anshul', 'arijit', 'arjun', 'arnav', 'aditi', 'astha', 'ashima', 'ayushi', 'bhavya', 'bhumika', 'bhumi', 'bhawna', 'chirag', 'dhruv', 'dhruvika', 'daksh', 'divyanshi', 'devanshu', 'dhruvi', 'gautam', 'gaurav', 'hitesh', 'harsh', 'ishita', 'ishika', 'ishit', 'ishaan', 'ish', 'ishwar', 'jitin', 'jagdish', 'jaya', 'janvi', 'jiya', 'kapil', 'kartik', 'kashish', 'kunal', 'komal', 'karan', 'kash', 'kavya', 'kavita', 'kamal', 'komal', 'laxmi', 'lakshmi', 'lalit', 'lalita', 'lokesh', 'lency', 'lara', 'mansi', 'manasvi', 'madhvi', 'madhuri', 'mohika', 'mohit', 'manav', 'mukesh', 'mehak', 'meghna', 'namira', 'naman', 'naina', 'nikhil', 'nikit', 'nikita', 'nimisha', 'oshika', 'poonam', 'poorvi', 'pooja', 'pankaj', 'pandit', 'prakash', 'prakhar', 'prasan', 'rashi', 'rashika', 'rajat', 'rashi', 'raghav', 'raman', 'rohan', 'riya', 'reena', 'rita', 'reema', 'ritika', 'rahul', 'raman', 'srishti', 'shristi', 'shrishti', 'somya', 'soumya', 'saumya', 'sonal', 'sonakshi', 'sonalika', 'saman', 'sagar', 'sahil', 'saraansh', 'sarthak', 'shipra', 'shilpa', 'shivani', 'shweta', 'satyam', 'shivam', 'shreshth', 'shiv', 'shiva', 'sunil', 'sambhav', 'sanya', 'sara', 'sarah', 'saloni', 'sonali', 'saurav', 'tarun', 'tanvi', 'tanya', 'taarika', 'tarika', 'urvashi', 'umang', 'varsha', 'vishal', 'vivek', 'vansh', 'varun', 'vanshika', 'vaibhav', 'yash', 'yashika']
for tg in data["intents"]:
    #theory ques
    if tg['tag'] == 'theory':
        all_tq = tg['patterns']
    #interview ques
    elif tg['tag'] == 'interview':
        all_fiq = tg['patterns']
        all_eiq = tg['responses']

theory_ques = []
problem_solving_ques = []
interview_ques = []

all_psq = []
skillset = []
name = ''
def test(skills, n):
    global all_psq
    global skillset
    global name
    name = n
    skillset.extend(skills)
    for i in skills:
        for tg in data["intents"]:
            if tg['tag'] == i:
                all_psq.extend(tg['patterns'])

que_list = ['How would you rate your competency in this JOB TITLE out of 10 ?', 'Do you prefer written or verbal communication ?', 'Your manager wants to choose/buy new software and hardware that will increase the productivity of their organisation and asks for your recommendation. How would you reply ?', 'Do you work best as alone or in a team ?', 'How do you feel working nights and weekends ?']
que_dict = {
    'How would you rate your competency in this JOB TITLE out of 10 ?': ['0 - 3', '4 - 6', '7 - 9', '10'],
    'Do you prefer written or verbal communication ?': ['Written', 'Verbal', 'Both of these', 'None of these'],
    'Your manager wants to choose/buy new software and hardware that will increase the productivity of their organisation and asks for your recommendation. How would you reply ?': ['Buy new hardware and software of same brand', 'Buy new hardware and software of different brands', 'Get a custom build of hardware and buy new software', 'Any other option'],
    'Do you work best as alone or in a team ?': ['Alone as best', 'In a team as best', 'Work best as a team leader', 'Can work in any way'],
    'How do you feel working nights and weekends ?': ['Yes, would love to', 'It depends on the work', 'Not possible', 'I want to, but I can not']
}
match = {
'0 - 3': 'out', '4 - 6': 'A capable applicant', '7 - 9': 'A hard-working applicant', '10': 'A self-confident applicant', 
'written': 'a good writer', 'verbal': 'a good speaker', 'both of these': 'possesses good communication skills',
'buy new hardware and software of different brands': 'a good problem solver', 'get a custom build of hardware and buy new software': 'an excellent analyser and has good decision making powers', 'any other option': 'thinks out of the box',
'alone as best': 'a one-man army', 'in a team as best': 'possesses good interpersonal relationship quality', 'work best as a team leader': 'capability to lead your team', 'can work in any way': 'adaptive in nature', 
'yes, would love to': 'dedicated towards work, comfortable working nights and weekends'}

exp = ''
def chat(inp, i):

    global exp
    inp = inp.lower()
    while True:
        if inp.lower() == "exit":
            return '5:over'

        #starting, meaning of name, haal chaal, ask the que: tell me about urself
        if i == 0:
            results = model.predict([bag_of_words(inp, words)])
            results_index = numpy.argmax(results)
            tag = labels[results_index]
            if tag == 'greeting':
                if name not in namesList:
                    return "0:Well, what's the meaning of your name "+name+" ?"
                else:
                    for tg in data["intents"]:
                        if tg['tag'] == tag:
                            responses = tg['responses']
                    return "0:"+random.choice(responses)

            elif tag == 'meaning':
                for tg in data["intents"]:
                    if tg['tag'] == tag:
                        responses = tg['responses']
                return "0:"+random.choice(responses)
            elif tag == 'thanks' or tag == 'iamfine':
                return "1:Good, so let’s start with a simple question - Tell me something about yourself ?"
            else:
                return "0:Sorry didn't get you."

        # asking exp
        elif i == 1:
            return "2:experience?"

        # choosing for tq or psq
        elif i == 2:
            exp = inp
            if exp == '0 - 1 year':
                return "3:"+get_tq()
            else:
                return "3:"+get_psq()

        # evaluating and asking theory/prac
        elif i == 3:
            if exp == '0 - 1 year':
                evaluate(theory_ques[len(theory_ques)-1], inp)
                if tq_no < 3:
                    return "3:"+get_tq()
                else:
                    theory_ques.clear()
                    que = get_iq(exp)
                    options = que_dict[que]
                    opt = '@'.join(options)
                    return "4:btnYou are doing great !\n"+que+"="+opt
            else:
                evaluate(problem_solving_ques[len(problem_solving_ques)-1], inp)
                if psq_no < 3:
                    return "3:"+get_psq()
                else:
                    problem_solving_ques.clear()
                    que = get_iq(exp)
                    options = que_dict[que]
                    opt = '@'.join(options)
                    return "4:btnGreat, I like your confidence !\n"+que+"="+opt

        #evaluating and asking interview
        elif i == 4:
            evaluate(interview_ques[len(interview_ques)-1], inp)
            if iq_no < 5:
                que = get_iq(exp)
                options = que_dict[que]
                opt = '@'.join(options)
                return "4:btn"+que+"="+opt
            else:
                if iq_no > 6:
                    interview_ques.clear()
                    return "5:over"
                else:    
                    return "4:"+get_iq(exp)

        else:
            return '5:over'

tq_no = 0
def get_tq():
    global tq_no
    y = random.choice(all_tq)
    if y not in theory_ques:
        level = dbI['tq:questions'][y]['level']
        if level == 'easy':
            tq_no = tq_no + 0.5
        else:
            tq_no = tq_no + 1
        theory_ques.append(y)
        return y
    else:
        return get_tq()

psq_no = 0
def get_psq():
    global psq_no
    y = random.choice(all_psq)
    if y not in problem_solving_ques:
        for i in skillset:
            if dbI['psq:'+i].get(y):
                level = dbI['psq:'+i][y]['level']
                break
        if level == 'easy':
            psq_no = psq_no + 0.5
        else:
            psq_no = psq_no + 1
        problem_solving_ques.append(y)
        return y
    else:
        return get_psq()

iq_no = 0
def get_iq(exp):
    global iq_no
    if iq_no < 5:
        q = que_list[iq_no]
        interview_ques.append(q)
        iq_no = iq_no + 1
        return q
    else:
        if exp == '0 - 1 year':
            y = random.choice(all_fiq)
        else:
            y = random.choice(all_eiq)
        if y not in interview_ques:
            iq_no = iq_no + 1
            interview_ques.append(y)
            return y
        else:
            return get_iq(exp)


marks = 0
int_skills = []
def evaluate(que, ans):
    global marks
    global int_skills

    if len(theory_ques) != 0:
        keywords = dbI['tq:questions'][que]['keywords']
        level = dbI['tq:questions'][que]['level']
        if any(word in ans for word in keywords):
            if len(theory_ques) == 1:
                marks = marks + 1
            else:
                if level == 'easy':
                    marks = marks + 1
                else:
                    marks = marks + 2
        else:
            marks = marks + 0

    elif len(problem_solving_ques) != 0:
        for i in skillset:
            if dbI['psq:'+i].get(que):
                keywords = dbI['psq:'+i][que]['keywords']
                level = dbI['psq:'+i][que]['level']
                break
        if any(word in ans for word in keywords):
            if len(problem_solving_ques) == 1:
                marks = marks + 1
            else:
                if level == 'easy':
                    marks = marks + 1
                else:
                    marks = marks + 2
        else:
            marks = marks + 0

    elif len(interview_ques) != 0:
        if match.get(ans):
            int_skills.append(match[ans])
            if ans == '10' or ans == 'Both of these' or ans == 'Yes, would love to':
                marks = marks + 1

def get_int_skills_and_marks():
    interview = []
    interview.append(marks+1)
    interview.append(exp)
    interview.extend(int_skills)
    return interview