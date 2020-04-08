
import os
from shutil import rmtree
from tempfile import mkdtemp

from flask import Flask, redirect, request, render_template, make_response, session, url_for
from flask_wtf import FlaskForm, csrf
from flask_wtf.file import FileField, FileRequired
from flask_wtf.file import FileField, FileRequired

from wtforms import IntegerField, RadioField, StringField
from wtforms.validators import DataRequired, NumberRange, Optional

from werkzeug.utils import secure_filename

from flask_dropzone import Dropzone


basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
dropzone = Dropzone(app)

app.config.update(
    UPLOADED_PATH=os.path.join(basedir, 'uploads'),
    # Flask-Dropzone config:
    DROPZONE_ENABLE_CSRF = True,
    DROPZONE_ALLOWED_FILE_CUSTOM = True,
    DROPZONE_ALLOWED_FILE_TYPE = 'text/*, .vwf, .txt',
    DROPZONE_REDIRECT_VIEW = 'uploaded',
)


app.secret_key = 'chiptoolskey'
csrf.CSRFProtect(app)

DELETE_TEMP_FILES = True or 'DELETE_TEMP_FILES' in os.environ




appname = __name__



@app.errorhandler(csrf.CSRFError)
def csrf_error(e):
    return e.description, 400

@app.route('/')
def root():
    return redirect(url_for('pwl'))


@app.route('/pwl', methods=('GET', 'POST'))
def pwl():
    if request.method == 'POST':
        f = request.files.get('file')
        vwf = os.path.join(app.config['UPLOADED_PATH'], secure_filename(f.filename))
        f.save(vwf)

        session['vwf'] = (vwf, f.filename)
        session['lastlocation'] = 'pwl POST'
        response = 'ok'
    else:
        if 'vwf' in session:
            response = ''
            session.pop('vwf', None)
        else:
            response = render_template('pwl.html')
    return response


@app.route('/uploaded')
def uploaded():
    if session.get('vwf') and session.get('lastlocation', None) == 'pwl POST':
        (vwf, vwfname) = session['vwf']
        pwl = vwf
        pwlname = vwfname

        doc = make_response(open(pwl, 'r').read())
        doc.headers['Content-Disposition'] = "attachment; filename=%s" % pwlname
        doc.mimetype = 'text/plain'
        response = doc
        session.pop('lastlocaton', None)
        session.pop('vwf', None)
        os.remove(vwf)
    else:
        response = redirect(url_for('pwl'))
    return response

