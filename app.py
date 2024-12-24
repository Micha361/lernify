from flask import Flask, request, jsonify, render_template, url_for, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_mail import Mail, Message
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import datetime
from datetime import timedelta
import openai
import requests
from PIL import Image
import pytesseract
import os
import urllib3
import warnings
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
import os
import requests
from flask import jsonify
from sqlalchemy import func
from flask_bcrypt import generate_password_hash
import firebase_admin
from firebase_admin import credentials, firestore
import json
from dotenv import load_dotenv
import time



warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)
 
app = Flask(__name__, static_folder="static", template_folder="templates")
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = '12648732321932'
 
from datetime import timedelta

app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7) 
app.config['REMEMBER_COOKIE_HTTPONLY'] = True  
app.config['REMEMBER_COOKIE_SECURE'] = True  
app.config['SESSION_COOKIE_DOMAIN'] = '.lernify.ch'  
app.config['REMEMBER_COOKIE_DOMAIN'] = '.lernify.ch'


firebase_key_env = os.getenv('FIREBASE_KEY')

if firebase_key_env:
    firebase_key = json.loads(firebase_key_env)
    cred = credentials.Certificate(firebase_key)
else:
    cred = credentials.Certificate("firebase_key.json")

firebase_admin.initialize_app(cred)

db = firestore.client()


bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = "strong" 
CORS(app, resources={r"/*": {"origins": "*"}})


openai.api_key = os.getenv('OPENAI_API_KEY')


class User(UserMixin): 
    def __init__(self, id, username, email, password, created_at, dark_mode=False, user_type="basic", last_login=None):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.created_at = created_at
        self.dark_mode = dark_mode
        self.user_type = user_type
        self.last_login = last_login

    @classmethod
    def from_firestore(cls, doc_id, data):
        return cls(
            id=doc_id,
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            created_at=data.get('created_at'),
            dark_mode=data.get('dark_mode', False),
            user_type=data.get('user_type', "basic"),
            last_login=data.get('last_login')
        )

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id




@login_manager.user_loader
def load_user(user_id):
    user_ref = db.collection('users').document(user_id).get()
    if user_ref.exists:
        user_data = user_ref.to_dict()
        return User.from_firestore(user_id, user_data)
    return None

 


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    email = StringField(validators=[InputRequired(), Email(), Length(max=120)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')
 
def validate_username(self, username):
    user_ref = db.collection('users').where('username', '==', username.data).stream()
    if any(user_ref):  
        raise ValidationError('Dieser Benutzername existiert bereits. Bitte wähle einen anderen aus.')

 
def validate_email(self, email):
    email_ref = db.collection('users').where('email', '==', email.data).stream()
    if any(email_ref): 
        raise ValidationError('Diese E-Mail existiert bereits. Bitte wähle eine andere aus.')

 
from wtforms import BooleanField

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Password"})
    remember = BooleanField("Angemeldet bleiben") 
    submit = SubmitField('Login')



@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('username')

    existing_user = db.collection('users').where('username', '==', username).stream()
    if any(existing_user):
        return jsonify({"message": "Benutzername existiert bereits"}), 400

    user_data = {
        'username': username,
        'email': data.get('email'),
        'created_at': datetime.utcnow()
    }
    db.collection('users').add(user_data)
    return jsonify({"message": "Benutzer hinzugefügt"}), 200


@app.route('/get_users', methods=['GET'])
def get_users():
    users_ref = db.collection('users')
    docs = users_ref.stream()
    users = [{doc.id: doc.to_dict()} for doc in docs]
    return jsonify(users), 200


@app.route('/update_user/<string:user_id>', methods=['POST'])
def update_user(user_id):
    data = request.get_json()
    user_ref = db.collection('users').document(user_id)
    user_ref.update(data)
    return jsonify({"message": "Benutzer aktualisiert"}), 200


@app.route('/delete_user/<string:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user_ref = db.collection('users').document(user_id)
    user_ref.delete()
    return jsonify({"message": "Benutzer gelöscht"}), 200

 
 
def create_openai_request(messages):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openai.api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": 300,
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=data, verify=False)
    response.raise_for_status()
    response_data = response.json()

    print("OpenAI Antwort:", json.dumps(response_data, indent=2))
    return response_data



@app.route('/api/user-registration-stats', methods=['GET'])
@login_required
def user_registration_stats():
    if current_user.username.lower() not in ["arber", "michael"]:
        return jsonify({'error': 'Zugriff verweigert'}), 403

    users_ref = db.collection('users').stream()
    stats = {}

    for user in users_ref:
        user_data = user.to_dict()
        created_at = user_data.get('created_at')
        if created_at:
            date = created_at.date().isoformat()
            stats[date] = stats.get(date, 0) + 1

    data = [{'date': date, 'count': count} for date, count in stats.items()]
    return jsonify(data)


@app.route('/api/delete-user/<string:user_id>', methods=['POST'])
@login_required
def delete_user_via_post(user_id):
    try:
        user_ref = db.collection('users').document(user_id)
        if user_ref.get().exists:
            user_ref.delete()
            return jsonify({"message": "Benutzer erfolgreich gelöscht"}), 200
        else:
            return jsonify({"message": "Benutzer nicht gefunden"}), 404
    except Exception as e:
        app.logger.error(f"Fehler beim Löschen des Benutzers: {e}")
        return jsonify({"message": "Fehler beim Löschen des Benutzers", "error": str(e)}), 500


@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    user_ref = db.collection('users').document(current_user.id).get()
    user_data = user_ref.to_dict()

    if not bcrypt.check_password_hash(user_data['password'], old_password):
        flash("Das alte Passwort ist falsch.", "danger")
        return redirect(url_for('account'))

    if new_password != confirm_password:
        flash("Die neuen Passwörter stimmen nicht überein.", "danger")
        return redirect(url_for('account'))

    db.collection('users').document(current_user.id).update({
        'password': bcrypt.generate_password_hash(new_password).decode('utf-8')
    })
    flash("Das Passwort wurde erfolgreich geändert.", "success")
    return redirect(url_for('account'))




@app.route('/admin/register-user', methods=['POST'])
def register_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    user_type = request.form.get('user_type')

    if not username or not email or not password or not user_type:
        flash('Alle Felder müssen ausgefüllt werden!', 'error')
        return redirect(url_for('admin'))

    user_ref = db.collection('users').where('email', '==', email).stream()
    if any(user_ref):
        flash('Ein Benutzer mit dieser Email existiert bereits!', 'error')
        return redirect(url_for('admin'))

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user_data = {
        'username': username,
        'email': email,
        'password': hashed_password,
        'user_type': user_type,
        'created_at': datetime.utcnow()
    }
    db.collection('users').add(new_user_data)

    send_welcome_email(username, email, password)
    flash('Benutzer erfolgreich registriert und E-Mail gesendet!', 'success')
    return redirect(url_for('admin'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_ref = db.collection('users').where('username', '==', form.username.data).stream()
        user_doc = next(user_ref, None)

        if user_doc:
            user_data = user_doc.to_dict()
            if bcrypt.check_password_hash(user_data['password'], form.password.data):
                user = User.from_firestore(user_doc.id, user_data)
                login_user(user, remember=form.remember.data)

                app.logger.info(f"Benutzer eingeloggt: {user.username}")
                if user.username.lower() in ["arber", "michael"]:
                    app.logger.info("Weiterleitung zu Admin-Bereich")
                    return redirect(url_for('admin'))
                else:
                    app.logger.info("Weiterleitung zu Lernify")
                    return redirect(url_for('lernify'))
            else:
                flash("Falsches Passwort, bitte versuche es nochmal.", "danger")
        else:
            flash("Benutzername existiert nicht", "danger")

    return render_template('login.html', form=form)






app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 465  
app.config['MAIL_USERNAME'] = 'lernify.ch@gmail.com' 
app.config['MAIL_DEFAULT_SENDER'] = 'lernify.ch@gmail.com'
app.config['MAIL_PASSWORD'] = 'hxcq xjjy lnmg undk'  
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEBUG'] = True  

mail = Mail(app)

def send_welcome_email(username, email, password):
    try:
        msg = Message(
            subject="Willkommen bei Lernify!",
            sender=app.config['MAIL_USERNAME'], 
            recipients=[email], 
        )
        msg.body = f"""
Willkommen bei Lernify, {username}!

Vielen Dank für deine Registrierung. Hier sind deine Zugangsdaten:

        Benutzername: {username}
        E-Mail: {email}
        Passwort: {password}

Bitte bewahre diese E-Mail sicher auf und ändere dein Passwort, falls du es nicht mehr sicher findest.

Viel Erfolg beim Lernen!
Dein Lernify Team
        """
        mail.send(msg)
        print("Willkommens-E-Mail wurde gesendet.")
    except Exception as e:
        print(f"Fehler beim Senden der Willkommens-E-Mail: {str(e)}")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data

        username_ref = db.collection('users').where('username', '==', username).stream()
        if any(username_ref):
            flash("Dieser Benutzername wird bereits verwendet. Bitte wähle einen anderen.", "danger")
            return render_template('register.html', form=form)

        email_ref = db.collection('users').where('email', '==', email).stream()
        if any(email_ref):
            flash("Diese E-Mail-Adresse wird bereits verwendet. Bitte wähle eine andere.", "danger")
            return render_template('register.html', form=form)

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        new_user = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'user_type': "free", 
            'created_at': datetime.utcnow()
        }
        db.collection('users').add(new_user)

        send_welcome_email(username, email, form.password.data)

        flash("Benutzer erfolgreich registriert! Bitte melde dich an.", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form=form)



@app.route('/api/set_dark_mode', methods=['POST'])
@login_required
def set_dark_mode():
    try:
        data = request.get_json()
        dark_mode = data.get('dark_mode', False)

        db.collection('users').document(current_user.id).update({
            'dark_mode': dark_mode
        })
        return jsonify({'success': True, 'dark_mode': dark_mode})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/get_dark_mode', methods=['GET'])
@login_required
def get_dark_mode():
    user_ref = db.collection('users').document(current_user.id).get()
    if not user_ref.exists:
        return jsonify({'dark_mode': False})
    user_data = user_ref.to_dict()
    return jsonify({'dark_mode': user_data.get('dark_mode', False)})
 
 
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('lernify'))
    return redirect(url_for('login'))

 
@app.route('/lernify', methods=['GET', 'POST'])
def lernify():
    return render_template('lernify.html', dark_mode=current_user.dark_mode)
 
 
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    app.logger.info(f"Benutzer {current_user.id} hat sich ausgeloggt. Dark Mode: {current_user.dark_mode}")
    logout_user()  

    response = redirect(url_for('login'))
    response.delete_cookie('remember_token', domain=app.config['REMEMBER_COOKIE_DOMAIN'])
    return response

 
 
@app.route('/marketplace', methods=['GET', 'POST'])
@login_required
def marketplace():
    return render_template('marketplace.html')
 
def premium_required(func):
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.user_type != "premium":
            flash("Nur für Premium-Benutzer zugänglich!", "danger")
            return redirect(url_for('lernify'))
        return func(*args, **kwargs)
    return wrapper

@app.route('/ordner', methods=['GET', 'POST'])
@login_required
def ordner():
    return render_template('ordner.html')


 
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    return render_template('account.html', user=current_user)
 
@app.route('/kontakt', methods=['GET', 'POST'])
@login_required
def kontakt():
    return render_template('kontakt.html', user=current_user)
 
@app.route('/troubleshooting', methods=['GET', 'POST'])
@login_required
def troubleshooting():
    return render_template('troubleshooting.html', user=current_user)

@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    return render_template('chatbot.html', user=current_user)
 
@app.route('/einleitung', methods=['GET', 'POST'])
@login_required
def einleitung():
    return render_template('einleitung.html', user=current_user)

@app.route('/faq', methods=['GET', 'POST'])
@login_required
def faq():
    return render_template('faq.html', user=current_user)

@app.route('/faq_input', methods=['GET', 'POST'])
@login_required
def faq_input():
    return render_template('faq_input.html', user=current_user)

@app.route('/AGB', methods=['GET', 'POST'])
def AGB():
    return render_template('AGB.html', user=current_user)

@app.route('/humanizer', methods=['GET', 'POST'])
def humanizer():
    return render_template('humanizer.html', user=current_user)

@app.route('/E-mail-aendern', methods=['GET', 'POST'])
@login_required
def E_mail_aendern():
    return render_template('E_mail_aendern.html', user=current_user)

@app.route('/passwort_aendern', methods=['GET', 'POST'])
@login_required
def passwort_aendern():
    return render_template('passwort_aendern.html', user=current_user)

@app.route('/zwei_faktor', methods=['GET', 'POST'])
@login_required
def zwei_faktor():
    return render_template('zwei_faktor.html', user=current_user)

@app.route('/account_admin', methods=['GET', 'POST'])
@login_required
def account_admin():
    return render_template('account_admin.html', user=current_user)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.user_type != "admin":
        flash("Du hast keinen Zugriff auf diese Seite.", "danger")
        return redirect(url_for('lernify'))

    users = db.collection('users').stream()
    users_list = [{"id": doc.id, **doc.to_dict()} for doc in users]  

    form = RegisterForm()

    if form.validate_on_submit():
        email_check = db.collection('users').where('email', '==', form.email.data).stream()
        username_check = db.collection('users').where('username', '==', form.username.data).stream()

        if any(email_check):
            flash("Diese E-Mail-Adresse wird bereits verwendet. Bitte wähle eine andere.", "danger")
        elif any(username_check):
            flash("Dieser Benutzername wird bereits verwendet. Bitte wähle einen anderen.", "danger")
        else:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            new_user = {
                "username": form.username.data,
                "email": form.email.data,
                "password": hashed_password,
                "user_type": "basic",
                "created_at": datetime.utcnow()
            }
            db.collection('users').add(new_user)
            flash("Benutzer erfolgreich registriert!", "success")
            return redirect(url_for('admin'))

    return render_template('lernify_admin.html', users=users_list, form=form)





@app.route('/summary', methods=['GET'])
@login_required
def summary():
    topic = request.args.get('topic', '')
   
    if not topic:
        return render_template('summary.html', summary='Kein Thema angegeben!')
   
    return render_template('summary.html', summary=f'Zusammenfassung des Themas: {topic}')
 

@app.route('/create_summary_from_files', methods=['POST'])
def create_summary_from_files():
    if 'files' not in request.files or len(request.files.getlist('files')) == 0:
        return jsonify({'error': 'Keine Dateien übermittelt oder Dateien fehlen.'}), 400

    files = request.files.getlist('files')
    content_list = []  

    try:
        for file in files:
            if file.mimetype == 'application/pdf':  
                reader = PdfReader(file)
                pdf_text = ''.join([page.extract_text() for page in reader.pages])
                content_list.append(pdf_text)
            else:  
                content = file.read().decode('utf-8')
                content_list.append(content)

        if not content_list:
            return jsonify({'error': 'Dateien sind leer oder enthalten keine lesbaren Daten.'}), 400

        combined_content = "\n".join(content_list)

        tone = request.args.get('tone', 'freundlich') 
        if tone == 'technisch':
            tone_instruction = "Erstelle eine präzise technische Zusammenfassung."
        elif tone == 'einfach':
            tone_instruction = "Erstelle eine leicht verständliche Zusammenfassung mit einfachen Worten."
        else:
            tone_instruction = "Erstelle eine freundliche und zugängliche Zusammenfassung."

        prompt = f"{tone_instruction}\n\n{combined_content}"
        messages = [{"role": "user", "content": prompt}]

        response = create_openai_request(messages)

        if 'choices' not in response or len(response['choices']) == 0:
            return jsonify({'error': 'Keine gültige Antwort von OpenAI erhalten.'}), 500

        summary = response['choices'][0]['message']['content'].strip()
        if not summary:
            return jsonify({'error': 'Die Antwort von OpenAI ist leer.'}), 500

        word_count = len(summary.split())
        summary += f"\n\nHinweis: Diese Zusammenfassung enthält ungefähr {word_count} Wörter."

        return jsonify({'summary': summary}), 200

    except Exception as e:
        app.logger.error(f"Fehler: {str(e)}")
        return jsonify({'error': f"Fehler: {str(e)}"}), 500




 
@app.route('/get_summary', methods=['POST'])
def get_summary():
    data = request.get_json()
    topic = data.get('topic', '')
    instructions = data.get('instructions', '')

    try:
        tone_instruction = "Bitte schreibe eine freundliche und zugängliche Zusammenfassung. Mache sie nicht zu kompliziert und benutze kein deutsches Doppel-S. Mache sie nicht zu kurz."

        prompt = f"{tone_instruction}\n\nThema: {topic}\n\n{instructions}"
        messages = [{"role": "user", "content": prompt}]
        response = create_openai_request(messages)

        if 'choices' not in response or len(response['choices']) == 0:
            return jsonify({"error": "Keine gültige Antwort von OpenAI erhalten."}), 500

        summary = response['choices'][0]['message']['content'].strip()
        if not summary:
            return jsonify({"error": "Die Antwort von OpenAI ist leer."}), 500

        word_count = len(summary.split())
        summary += f"\n\n\n- Wörter: {word_count}"

        return jsonify({'summary': summary, 'tone_used': 'freundlich'}), 200

    except Exception as e:
        app.logger.error(f"Fehler bei der Verarbeitung der Anfrage: {e}")
        return jsonify({'error': f"Fehler bei der Verarbeitung der Anfrage: {str(e)}"}), 500






 
def send_deletion_email(user_email):
    """E-Mail-Benachrichtigung nach Löschung des Accounts senden."""
    try:
        msg = Message(
            "Account gelöscht",
            sender='lernify.ch@gmail.com',  
            recipients=[user_email],
            body=(
                "Ihr Account wurde erfolgreich gelöscht! "
                "Bitte informiere uns doch, was dich dazu bewegt hat, den Account zu löschen, um diese Mängel zu verbessern.\n\n"
                "Mit freundlichen Grüssen,\nLernify"
            )
        )
        mail.send(msg)
        app.logger.info(f"E-Mail erfolgreich an {user_email} gesendet.")
    except Exception as e:
        app.logger.error(f"Fehler beim Senden der Lösch-E-Mail: {e}")


@app.route('/api/delete-account', methods=['DELETE'])
@login_required
def delete_account():
    try:
        user_id = current_user.id
        user_email = current_user.email

        user_ref = db.collection('users').document(str(user_id))
        user_ref.delete()

        send_deletion_email(user_email)
        return jsonify({'message': 'Account erfolgreich gelöscht'}), 200
    except Exception as e:
        app.logger.error(f"Fehler beim Löschen des Accounts: {e}")
        return jsonify({'message': 'Fehler beim Löschen des Accounts', 'error': str(e)}), 500



def delete_user_from_db(user_id):
    try:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            app.logger.info(f"Benutzer mit ID {user_id} erfolgreich gelöscht.")
        else:
            app.logger.warning(f"Benutzer mit ID {user_id} wurde nicht gefunden.")
            raise ValueError("Benutzer nicht gefunden.")
    except Exception as e:
        app.logger.error(f"Fehler in delete_user_from_db: {e}")
        raise

last_request_time = {}

@app.route('/generate_question', methods=['POST'])
def generate_question():
    try:
        data = request.json
        user_id = data.get('user_id', 'unknown')
        notes = data.get('notes', '').strip()

        if not notes:
            return jsonify({"error": "Notizen dürfen nicht leer sein."}), 400

        now = time.time()
        cooldown_period = 5
        if user_id in last_request_time and now - last_request_time[user_id] < cooldown_period:
            remaining_time = cooldown_period - (now - last_request_time[user_id])
            return jsonify({
                "error": f"Du bist zu schnell! Bitte warte noch {remaining_time:.1f} Sekunden."
            }), 429

        last_request_time[user_id] = now

        prompt = f"""
Basierend auf den folgenden Notizen, generiere eine einzigartige Quizfrage mit vier Antwortmöglichkeiten.
Variiere die Formulierung der Frage und Antworten, um ähnliche Ergebnisse zu vermeiden. 
Die Frage sollte kreativ und herausfordernd sein. Wiederhole nie eine Frage, alle Fragen sollen einzigartig sein.
Auch sollen die Fragen nicht ähnlich sein.

Notizen:
{notes}

Format:
Frage: [Die Quizfrage]
Antworten:
1. [Antwort A]
2. [Antwort B]
3. [Antwort C]
4. [Antwort D]
Richtige Antwort: [1/2/3/4]
"""
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0.9,
                "top_p": 1.0
            },
            verify=False
        )

        response.raise_for_status()
        response_data = response.json()

        if 'choices' not in response_data or not response_data['choices']:
            return jsonify({"error": "Keine gültige Antwort von OpenAI erhalten."}), 500

        content = response_data['choices'][0]['message']['content'].strip()
        if not content or "Frage:" not in content or "Antworten:" not in content or "Richtige Antwort:" not in content:
            return jsonify({"error": "Unvollständige Antwort erhalten."}), 500

        lines = content.split("\n")
        question = lines[0].replace("Frage: ", "").strip()
        answers = [line.split(". ", 1)[1] for line in lines[2:6]]
        correct_index = int(lines[-1].split(": ")[1]) - 1

        return jsonify({
            "question": question,
            "answers": answers,
            "correct_index": correct_index
        }), 200

    except Exception as e:
        app.logger.error(f"Fehler in der Funktion generate_question: {str(e)}")
        return jsonify({"error": f"Serverfehler: {str(e)}"}), 500


@app.route('/humanizer/generate', methods=['POST'])
@login_required
def generate_humanized_text():
    data = request.get_json()
    notes = data.get('notes', '')

    if not notes:
        return jsonify({"error": "Keine Notizen übermittelt."}), 400

    try:
        prompt = f"""
Humanisiere den folgenden Text so, dass er lebendig, angenehm und natürlich klingt:
{notes}

Vermeide technische Formulierungen, nutze einen freundlichen Ton.
Benutze auch kein Deutsches ß.
"""

        messages = [{"role": "user", "content": prompt}]
        response = create_openai_request(messages)

        if 'choices' not in response or not response['choices']:
            return jsonify({"error": "Fehler bei OpenAI-Anfrage"}), 500

        humanized_text = response['choices'][0]['message']['content'].strip()
        return jsonify({"humanized_text": humanized_text}), 200

    except Exception as e:
        app.logger.error(f"Fehler in generate_humanized_text: {str(e)}")
        return jsonify({"error": f"Fehler beim Erstellen des Textes: {str(e)}"}), 500


if __name__ == "__main__":
    print("Arbeitsverzeichnis:", os.getcwd())
    app.run(debug=True)