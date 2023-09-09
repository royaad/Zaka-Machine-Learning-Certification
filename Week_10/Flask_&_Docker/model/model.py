import os
# hide TF warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import numpy as np
import string, re, pickle, logging
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model

class Translator:

    def __init__(self, model_directory='./'):
        logging.info("Translator Initialized")
        self.directory = model_directory
        self.model = load_model(self.directory+'EN_FR_Translator.h5')
        logging.info("Model is loaded!")

    def predict(self, in_sentence, in_language='EN', out_language='FR', Max_Length=21):
        in_sentence = self.text_cleaner(in_sentence)
        X = self.Encoder(in_sentence, in_language, Max_Length)
        Y = np.ravel(np.argmax(self.model.predict(X, verbose=0), axis=2))
        out_sentence = self.logits_to_text(Y, out_language)
        out_sentence = out_sentence.replace('<pad>', '')
        return out_sentence.strip()
    
    def text_cleaner(self, sentence):
        sentence = sentence.lower()
        translation_table = str.maketrans("", "", string.punctuation)
        sentence = re.sub(r"(?<!\d)[- \'](?!\d)", ' ', sentence)
        sentence = sentence.translate(translation_table)
        return sentence

    def Encoder(self, sentence, language, length=21):
        #integer encode sequences
        seq = self.text_to_seq(sentence, language)
        #pad sequences with 0 values
        seq = pad_sequences([seq], maxlen=length, padding='post')
        return seq
    
    def logits_to_text(self, logits, language):

        word_index = self.word_index_dict(language)
        index_word = dict(zip(word_index.values(), word_index.keys()))
        index_word[0] = '<pad>'

        return ' '.join([index_word[prediction] for prediction in logits])
    
    def word_index_dict(self, language):
        if language == 'EN':
            pickle_dict = open(self.directory+"EN_dict.pickle", "rb")
            dictionary = pickle.load(pickle_dict)
            return dictionary
        elif language == 'FR':
            pickle_dict = open(self.directory+"FR_dict.pickle", "rb")
            dictionary = pickle.load(pickle_dict)
            return dictionary
        else:
            print('Input Language Does Not Exist')

    def text_to_seq(self, sentence, language):
        sentence = sentence.split()
        seq = []
        word_index = self.word_index_dict(language)
        #OOVs are dropped
        for x in sentence:
            try:
                seq.append(word_index[x])
            except:
                pass
        return seq

def main():
    model = Translator()
    translation = model.predict("She is driving the truck.")
    logging.info("French Translation:\t{}".format(translation))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
