
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

# placeholder
def vwf2pwl(infile):
    return infile



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
        filepath = os.path.join(app.config['UPLOADED_PATH'], secure_filename(f.filename))
        f.save(filepath)
        session['upload'] = (filepath, f.filename)
        session['app'] = 'pwl'
        response = 'ok'
    else:
        if 'upload' in session:
            #cleanup stale session
            session.pop('upload', None)
            session.pop('app', None)

        response = render_template('pwl.html')
    return response


@app.route('/uploaded')
def uploaded():
    referrer = session.pop('app', None)
    (inpath, inname) = session.pop('upload', (None, None))

    missing_context = ((referrer is None), (inpath is None), (inname is None))

    if all(missing_context):
        # not sure how we got here
        return redirect(url_for('/'))
    elif any(missing_context):
        # anything missing is an application error
        raise TypeError(f'Incomplete session referrer: {referrer}, upload: ({inpath}, {inname})')

    # process the file according to the app
    try:
        if referrer == 'pwl':
            # render from vwf to pwl file
            outpath = vwf2pwl(inpath)
            # TODO: better rename detection
            outname = inpath.replace('.vwf', '.pwl')
        else:
            raise TypeError(f'Unknown referrer: {referrer}')
    except:
        if DELETE_TEMP_FILES:
            os.remove(inpath)

    doc = make_response(open(outpath, 'r').read())
    doc.headers['Content-Disposition'] = "attachment; filename=%s" % outname
    doc.mimetype = 'text/plain'
    response = doc

    if DELETE_TEMP_FILES:
        os.remove(outpath)

    return response

