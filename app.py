from flask import Flask, render_template, redirect, url_for, session,request, flash, jsonify
import openai
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
import bcrypt
from dotenv import load_dotenv
load_dotenv()
import os
from flask_mysqldb import MySQL
openai.api_key = os.getenv("OPENAI_API_KEY") 
app = Flask(__name__)

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
#   print("prompt:", prompt)
#   response = openai.Image.create(prompt=prompt, n=1, size="256x256") 
#   print(response)
#   return jsonify(response)
    try:
        # Assuming you have the correct OpenAI library and API key set up
        response = openai.Image.create(prompt=prompt, n=1, size="256x256")
        images = [result['url'] for result in response['data']]
        return jsonify({"success": True, "images": images})
    except Exception as e:
        error_message = str(e)
        print("Error:", error_message)
        return jsonify({"success": False, "error": error_message})



if __name__ == '__main__':
    app.run(debug=True)