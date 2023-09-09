import os, logging

from flask import Flask, render_template, request
from model.model import Translator

app = Flask(__name__)

# define model path
model_directory = './model/'

# create instance
model = Translator(model_directory)
logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET', 'POST'])
#the get method is essential to run the html page.
def index():
    if request.method == 'POST':
        text = request.form['input-text']
        # Process the text input here
        text_out = model.predict(text)
        return render_template('ZAKA.html', result=text_out)
    #the next chunk handles the get method
    #after 8000 write ?text='SHe is driving the truck'
    #We will get back an answer but not the english sentence
    #Some changes were made on the html file in order to return the english sentence
    text = request.args.get("text")
    if text:
        text_out = model.predict(text)
        return render_template('ZAKA.html', result=text_out)
    return render_template('ZAKA.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
