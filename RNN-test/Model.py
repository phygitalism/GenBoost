import numpy as np
import json
from mnistprob import mnist_net
from genboost import genboost
import time
from ElephantSender import sendNotification
import sys

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense, Activation, Embedding
from keras.layers import LSTM, SpatialDropout1D
from keras.datasets import imdb


# Устанавливаем seed для повторяемости результатов
np.random.seed(42)
# Максимальное количество слов (по частоте использования)
max_features = 5000
# Максимальная длина рецензии в словах
maxlen = 80

# Загружаем данные
(X_train, y_train), (X_test, y_test) = imdb.load_data(num_words=max_features)

# Заполняем или обрезаем рецензии
X_train = sequence.pad_sequences(X_train, maxlen=maxlen)
X_test = sequence.pad_sequences(X_test, maxlen=maxlen)

del X_train
del y_train

# Создаем сеть
model = Sequential()
# Слой для векторного представления слов
model.add(Embedding(max_features, 32))
model.add(SpatialDropout1D(0.2))
# Слой долго-краткосрочной памяти
model.add(LSTM(100, dropout=0.2, recurrent_dropout=0.2)) 
# Полносвязный слой
model.add(Dense(1, activation="sigmoid"))

model.compile(optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy'])

def eval_model(weights):
    weight_layer_one = np.array(weights[:5000*32]).reshape(5000,32) # weights[:784*512]).reshape(784,512)
    weight_layer_two = np.array(weights[5000*32:(5000*32 +32*400)]).reshape(32,400)
    # 5000*32 +32*400 = 172800
    weight_layer_three = np.array(weights[172800:172800+100*400]).reshape(100,400)
    weight_layer_four = np.array(weights[172800+100*400:172800+101*400]).reshape(400,)
    # 172800+101*400 = 213200
    weight_layer_five = np.array(weights[213200:213200 + 100 * 1]).reshape(100,1)
    weight_layer_six = np.array(weights[-1]).reshape(1,)
    
    model.set_weights([
        weight_layer_one,
        weight_layer_two,
        weight_layer_three,
        weight_layer_four,
        weight_layer_five,
        weight_layer_six
    ])
    
    return np.array([-1.*model.evaluate(X_test, y_test,verbose=0 )[1]])

with open('parameters_3.json') as json_data:
    params = json.load(json_data)

MyProb = mnist_net(fit_func=eval_model,dim=213200 + 100 * 1 + 1,lb=-1.,rb=1.)
gb = genboost(problem=MyProb)

results = []
times = []
TotalTime_0 = time.time()

for i, param in enumerate(params):
    t0 = time.time()
    print("Star of test #{}.".format(i+1))
    pop = gb.run(param)
    results.append(pop.champion_f)
    print('Parameters: {}'.format(param))
    print('Fitness: {}'.format(pop.champion_f))
    t1 = time.time() - t0
    times.append(t1)
    print("Time for test:{}".format(t1 / 60))
    print('-'*20)
print("Total time for all tests:{}".format(time.time() - TotalTime_0))

def_stdout = sys.stdout
sys.stdout = open('log.txt','w')
for i, (param, fitness, TestTime) in enumerate(zip(params,results,times)):
    print("Test #{}".format(i+1))
    print('Parameters: {}'.format(param))
    print('Fitness: {}'.format(fitness))
    print("Time for test:{}".format(TestTime / 60.))
    print('-'*20)
sys.stdout = def_stdout

template = 'Test #{}\nParameters: {}\nFitness: {}\nTime: {}\n'
for i, (param, fitness, TestTime) in enumerate(zip(params,results,times)):
    sendNotification(template.format(i+1,param, fitness, TestTime/60.))
