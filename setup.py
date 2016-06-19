from distutils.core import setup
setup(
  name = 'starpath',
  py_modules=['starpath'],
  scripts=['starpath.py'],
  version = '1.2.1',
  description = 'JSON Pointers with wildcards!',
  author = 'Arnaud Dagnelies',
  author_email = 'arnaud.dagnelies@gmail.com',
  url = 'https://github.com/dagnelies/starpath',
  keywords = ['path', 'json', 'pointer', 'wildcard'],
  classifiers = []
)