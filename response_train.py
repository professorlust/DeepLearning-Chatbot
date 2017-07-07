from keras.models import Model
from keras.preprocessing import sequence
from keras.layers.recurrent import LSTM
from keras.layers import Dense, Dropout, Embedding, Input
from keras.utils.data_utils import get_file

import numpy as np
import random
import sys
import os

path = "data/text_generation/dialogues_edit" #path to training data, preferably saved as a .txt file.

try: 
    text = open(path).read().lower()
except UnicodeDecodeError:
    import codecs
    text = codecs.open(path, encoding='utf-8').read().lower()

print('corpus length:', len(text))

chars = set(text)
words = set(open(path).read().lower().split())


print("Unique words",len(words))
print("Unique chars", len(chars))


word_indices = dict((c, i) for i, c in enumerate(words))
indices_word = dict((i, c) for i, c in enumerate(words))

maxlen = 50
step = 3
print("maxlen:",maxlen,"step:", step)
sentences = []
next_words= []
sentences1 = []
list_words = []

sentences2=[]
list_words=text.lower().split()


for i in range(0,len(list_words)-maxlen, step):
    sentences2 = ' '.join(list_words[i: i + maxlen])
    sentences.append(sentences2)
    next_words.append((list_words[i + maxlen]))
print('Length of sentences:', len(sentences))

print('Vectorization...')
X = np.zeros((len(sentences), maxlen, len(words)), dtype=np.bool)
y = np.zeros((len(sentences), len(words)), dtype=np.bool)
for i, sentence in enumerate(sentences):
    for t, word in enumerate(sentence.split()):
        X[i, t, word_indices[word]] = 1
    y[i, word_indices[next_words[i]]] = 1


#build the model: 2 stacked LSTM cells
sequence = Input(shape=(maxlen,len(words)), dtype='float32', name='input')
forwards1 = LSTM(256, return_sequences=True, dropout=0.1, recurrent_dropout=0.1)(sequence)
after_dp1 = Dropout(0.4)(forwards1)
forwards2 = LSTM(256, return_sequences=False, dropout=0.1, recurrent_dropout=0.1)(sequence)
after_dp2 = Dropout(0.5)(forwards2)
output = Dense(len(words), activation='softmax', name='activation')(after_dp2)

model = Model(inputs=sequence, outputs=output)

model.compile(loss='categorical_crossentropy', optimizer='adam')

#Comment out the below lines if this is the first time you're training on new data.
if os.path.isfile('backup/response_models/TextGeneration'):
    model.load_model('backup/response_models/TextGeneration.h5')

def sample(a, temperature=1.0):
    # helper function to sample an index from a probability array
	a = np.log(a) / temperature
	dist = np.exp(a)/np.sum(np.exp(a))
	choices = range(len(a))
	return np.random.choice(choices, p=dist)

# train the model, output generated text after each iteration
no_of_iterations = 20

for iteration in range(1, no_of_iterations):
    print()
    print('-' * 50)
    print('Iteration', iteration)
    model.fit(X, y, batch_size=640, epochs=3)
    model.save('backup/response_models/Textweights.h5',overwrite=True)

    start_index = random.randint(0, len(list_words) - maxlen - 1)

    for diversity in [0.3,0.6, 1.3, 1.6, 1.9]:
        print()
        print('Diversity:', diversity)
        generated = ''
        sentence = list_words[start_index: start_index + maxlen]
        generated += ' '.join(sentence)
        print('Seed: "' , sentence , '"')
        print()
        sys.stdout.write(generated)
        print()

        for i in range(200):
            x = np.zeros((1, maxlen, len(words)))
            for t, word in enumerate(sentence):
                x[0, t, word_indices[word]] = 1.

            preds = model.predict(x, verbose=0)[0]
            next_index = sample(preds, diversity)
            next_word = indices_word[next_index]
            generated += next_word
            del sentence[0]
            sentence.append(next_word)
            sys.stdout.write(' ')
            sys.stdout.write(next_word)
            sys.stdout.flush()
        print()
