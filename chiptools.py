

from datetime import datetime, timezone
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

from vwf2pwl import vwf2pwl


basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
dropzone = Dropzone(app)

app.config.update(
    UPLOADED_PATH = os.path.join(basedir, 'uploads'),
    DELETE_TEMP_FILES = False,
    # Flask-Dropzone config:
    DROPZONE_ENABLE_CSRF = True,
    DROPZONE_ALLOWED_FILE_CUSTOM = True,
    DROPZONE_ALLOWED_FILE_TYPE = 'text/*, .vwf, .txt',
    DROPZONE_REDIRECT_VIEW = 'uploaded',
)


app.secret_key = 'chiptoolskey'
csrf.CSRFProtect(app)


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
        prefix = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%S.%f')
        savename = prefix + '_' + secure_filename(f.filename)
        filepath = os.path.join(app.config['UPLOADED_PATH'], savename)
        f.save(filepath)
        session['upload'] = (filepath, f.filename)
        session['app'] = 'pwl'
        response = 'ok'
        print(f'Upload: {savename}')
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
        return redirect(url_for('root'))
    elif any(missing_context):
        # anything missing is an application error
        raise TypeError(f'Incomplete session referrer: {referrer}, upload: ({inpath}, {inname})')

    # process the file according to the app
    try:
        if referrer == 'pwl':
            # render from vwf to pwl file
            outname = inname.replace('.vwf', '.pwl')  # TODO: make better
            outpath = vwf2pwl(inpath)
        else:
            raise TypeError(f'Unknown referrer: {referrer}')
    except:
        raise

    doc = make_response(open(outpath, 'r').read())
    doc.headers['Content-Disposition'] = "attachment; filename=%s" % outname
    doc.mimetype = 'text/plain'
    response = doc

    if app.config['DELETE_TEMP_FILES']:
        os.remove(inpath)
        os.remove(outpath)

    return response

