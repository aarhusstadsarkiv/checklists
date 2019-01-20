import sys
from pathlib import Path

import markdown
import yaml

from flask import Flask, render_template, url_for, abort
from werkzeug.utils import cached_property
from flask_frozen import Freezer


DOCS_EXTENSION = '.md'

class Document:
    def __init__(self, filepath):
        """Filepath is a Path-object"""
        self.filepath = filepath
        self.filestem = self.filepath.stem
        self.url = str(self.filepath).rsplit('.', maxsplit=1)[0]
        self.published = False  # overridden later by metadata from .md-files
        self._initialize_metadata()

    @cached_property
    def content(self):
        with open(self.filepath, 'r') as f:
            content = f.read().split('\n\n', 1)[1].strip()
        return markdown.markdown(content)

    def _initialize_metadata(self):
        meta_str = ''
        with open(self.filepath, 'r') as f:
            for l in f:
                if not l.strip():
                    break
                meta_str += l
        self.__dict__.update(yaml.load(meta_str))


class Collection:
    def __init__(self, filedir):
        self.filedir = filedir
        self.file_ext = DOCS_EXTENSION
        self._cache = {}
        self._initialize_cache()
    
    @property
    def list(self):
        if app.debug:
            return self._cache.values()
        else:
            return [doc for doc in self._cache.values() if doc.published]

    def get(self, filepath):
        try:
            return self._cache[filepath]
        except KeyError:
            abort(404)

    def _initialize_cache(self):
        for f in Path(self.filedir).glob('*.*'):
            if f.suffix == self.file_ext:
                doc = Document(f)
                self._cache[doc.filestem] = doc


app = Flask(__name__)
app.config['FREEZER_DESTINATION'] = 'docs'
procedures = Collection('procedures')
contracts = Collection('contracts')

# Last call before routes, maybe not necessary
freezer = Freezer(app)

@app.route('/')
def index():
    context = {}
    context['procedures'] = procedures.list
    context['contracts'] = contracts.list
    return render_template('index.html', **context)

@app.route('/procedures/<path:path>/')
def get_procedure(path):
    return render_template('procedure.html', procedure=procedures.get(path))

@app.route('/contracts/<path:path>/')
def get_contract(path):
    return render_template('contract.html', contract=contracts.get(path))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'build':
        freezer.freeze()
    else:
        app.run(port=8000, debug=True)
