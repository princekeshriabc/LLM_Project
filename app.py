from flask import Flask, render_template, redirect, url_for, session,request, flash, jsonify
import openai
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
import bcrypt
from dotenv import load_dotenv
load_dotenv()
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from flask_mysqldb import MySQL
openai.api_key = os.getenv("OPENAI_API_KEY") 
app = Flask(__name__)

# Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key
llm = OpenAI(openai_api_key=openai.api_key, temperature=0.6)

# Define the prompt template with five input variables
prompt_template = PromptTemplate(
    input_variables=['word1', 'word2', 'word3', 'word4', 'word5'],
    template="make a good story following this natural flow, adhering to common sense logic, and being captivating to the reader and use the this words {word1} {word2} {word3} {word4} {word5} and complete the story entirely"
)

# Assuming you have already defined the 'llm' variable
chain = LLMChain(llm=llm, prompt=prompt_template)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'mydatabase'
app.secret_key = 'your_secret_key_here'

mysql = MySQL(app)

class RegisterForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self,field):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users where email=%s",(field.data,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            raise ValidationError('Email Already Taken')

class LoginForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")



@app.route('/',methods=['GET','POST'])
def index():
    return render_template('index.html')


@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

        # store data into database 
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",(name,email,hashed_password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('register.html',form=form)

@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = cursor.fetchone()
        cursor.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            flash("Login failed. Please check your email and password")
            return redirect(url_for('login'))

    return render_template('login.html',form=form)

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users where id=%s",(user_id,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            return render_template('dashboard.html',user=user)
            
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out successfully.")
    return redirect(url_for('login'))

# @app.route('/Story', methods=['GET', 'POST'])
# def Story():
#     if request.method == 'POST':
#         # Get input words from the user
#         input_words = [request.form[f'word{i}'] for i in range(1, 6)]

#         # Generate the story using user input words
#         story = chain.run(word1=input_words[0], word2=input_words[1], word3=input_words[2], word4=input_words[3], word5=input_words[4])

#         return render_template('Story.html', story=story)

#     return render_template('Story.html')


@app.route('/Story', methods=['GET', 'POST'])
def Story():
    if request.method == 'POST':
        # Get input words from the user
        input_words = [request.form[f'word{i}'] for i in range(1, 6)]

        # Generate the story using user input words
        story = chain.run(word1=input_words[0], word2=input_words[1], word3=input_words[2], word4=input_words[3], word5=input_words[4])

        return render_template('Story.html', story=story)

    return render_template('Story.html')


@app.route('/generate-answer', methods=['POST','GET'])
def generate_answer():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')

        # Use the OpenAI API to generate a text-based response
        response = openai.Completion.create(
            engine="text-davinci-003",  # You can choose the engine that best fits your needs
            prompt=prompt,
            max_tokens=150  # You can adjust this parameter based on your preference
        )

        answer = response.choices[0].text.strip()
        return jsonify({"success": True, "answer": answer})
    except Exception as e:
        error_message = str(e)
        print("Error:", error_message)
        return jsonify({"success": False, "error": error_message})
    
@app.route('/generateimages/<prompt>')
def generate(prompt):
  print("prompt:", prompt)
  response = openai.Image.create(prompt=prompt, n=1, size="256x256") 
  print(response)
  return jsonify(response)
    # try:
    #     # Assuming you have the correct OpenAI library and API key set up
    #     response = openai.Image.create(prompt=prompt, n=1, size="256x256")
    #     images = [result['url'] for result in response['data']]
    #     return jsonify({"success": True, "images": images})
    # except Exception as e:
    #     error_message = str(e)
    #     print("Error:", error_message)
    #     return jsonify({"success": False, "error": error_message})



if __name__ == '__main__':
    app.run(debug=True)