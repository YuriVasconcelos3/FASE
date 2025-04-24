from flask import Flask, render_template, url_for, session, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from authlib.integrations.flask_client import OAuth
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
admin = Admin(app, name='Admin', template_mode='bootstrap3')
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id='363377690507-22qg5phfvj40rbjflefqfpuapa1pput7.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v3/',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'
    },
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
    issuer='https://accounts.google.com'
)

instagram = oauth.register(
    name='instagram',
    client_id='seu-client-id-instagram',
    client_secret='seu-client-secret-instagram',
    access_token_url='https://api.instagram.com/oauth/access_token',
    authorize_url='https://api.instagram.com/oauth/authorize',
    api_base_url='https://graph.instagram.com/',
    client_kwargs={'scope': 'user_profile,user_media'},
)


class BackgroundImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    titulo = db.Column(db.String(150), nullable=True) 
    subtitulo = db.Column(db.Text, nullable=True) 

class CarouselItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False) 
    image = db.Column(db.String(150), nullable=False)

class Patrocinador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    imagem = db.Column(db.String(150), nullable=False)
    url = db.Column(db.String(150))  # Opcional: link para o site do patrocinador

class Palestrante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    imagem = db.Column(db.String(150), nullable=False)

class Depoimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    comentario = db.Column(db.Text, nullable=False)
    foto = db.Column(db.String(150), nullable=False)
    curso = db.Column(db.String(100), nullable=True)

class BackgroundImageView(ModelView):
    form_columns = ['filename', 'titulo', 'subtitulo']
    form_overrides = {
        'filename': FileUploadField
    }
    form_args = {
        'filename': {
            'label': 'Imagem de Fundo',
            'base_path': app.config['UPLOAD_FOLDER'],
            'allow_overwrite': False
        }
    }

class CarouselItemView(ModelView):
    form_columns = ['title', 'description', 'image']
    form_overrides = {
        'image': FileUploadField
    }
    form_args = {
        'image': {
            'label': 'Imagem do Slide',
            'base_path': app.config['UPLOAD_FOLDER'],
            'allow_overwrite': False
        }
    }

class PatrocinadorView(ModelView):
    form_columns = ['nome', 'imagem', 'url']
    form_overrides = {
        'imagem': FileUploadField
    }
    form_args = {
        'imagem': {
            'label': 'Logo do Patrocinador',
            'base_path': app.config['UPLOAD_FOLDER'],
            'allow_overwrite': False
        }
    }

class PalestranteView(ModelView):
    form_columns = ['nome', 'descricao', 'imagem']
    form_overrides = {
        'imagem': FileUploadField
    }
    form_args = {
        'imagem': {
            'label': 'Imagem do Palestrante',
            'base_path': app.config['UPLOAD_FOLDER'],
            'allow_overwrite': False
        }
    }

class DepoimentoView(ModelView):
    form_columns = ['nome', 'comentario', 'foto', 'curso']
    form_overrides = {
        'foto': FileUploadField
    }
    form_args = {
        'foto': {
            'label': 'Foto do Autor',
            'base_path': app.config['UPLOAD_FOLDER'],
            'allow_overwrite': False
        }
    }


admin.add_view(BackgroundImageView(BackgroundImage, db.session))
admin.add_view(CarouselItemView(CarouselItem, db.session))
admin.add_view(PatrocinadorView(Patrocinador, db.session))
admin.add_view(PalestranteView(Palestrante, db.session))
admin.add_view(DepoimentoView(Depoimento, db.session))

@app.route('/auth/google')
def google_auth():
    comentario = request.args.get('comentario', '')
    session['pending_comment'] = comentario
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_authorize():
    try:
        token = google.authorize_access_token()
        if token is None:
            return "Falha ao obter token de acesso", 400
        
        # Obtém as informações do usuário
        user_info = google.parse_id_token(token, nonce=None)
        
        if 'pending_comment' in session:
            # Salva a foto do Google no servidor
            picture_url = user_info.get('picture')
            if picture_url:
                import requests
                from werkzeug.utils import secure_filename
                import uuid
                
                try:
                    response = requests.get(picture_url)
                    if response.status_code == 200:
                        # Gera um nome único para o arquivo
                        filename = f"google_{uuid.uuid4().hex}.jpg"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        
                        # Salva a imagem
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        # Cria o depoimento com a foto
                        novo_depoimento = Depoimento(
                            nome=user_info.get('name', 'Usuário Google'),
                            comentario=session['pending_comment'],
                            foto=filename,
                            curso=None
                        )
                except Exception as e:
                    print(f"Erro ao baixar foto do Google: {str(e)}")
                    # Se falhar, cria sem foto
                    novo_depoimento = Depoimento(
                        nome=user_info.get('name', 'Usuário Google'),
                        comentario=session['pending_comment'],
                        foto='', 
                        curso=None
                    )
            else:
                novo_depoimento = Depoimento(
                    nome=user_info.get('name', 'Usuário Google'),
                    comentario=session['pending_comment'],
                    foto='', 
                    curso=None
                )
            
            db.session.add(novo_depoimento)
            db.session.commit()
            session.pop('pending_comment', None)
        
        return redirect(url_for('home'))
    except Exception as e:
        return f"Erro durante a autenticação: {str(e)}", 400

@app.route('/')
def home():
    background_image = BackgroundImage.query.first()
    background_url = url_for('static', filename=f'uploads/{background_image.filename}') if background_image else None
    carousel_items = CarouselItem.query.all()
    patrocinadores = Patrocinador.query.all()
    palestrantes = Palestrante.query.all()
    depoimentos = Depoimento.query.all()
    return render_template('index.html', 
                         background_url=background_url,
                         background_image=background_image,
                         carousel_items=carousel_items, 
                         palestrantes=palestrantes,
                         patrocinadores=patrocinadores,
                         depoimentos=depoimentos)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)