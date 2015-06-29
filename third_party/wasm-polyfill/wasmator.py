'''
Receives an emscripten output, and integrates the polyfill

XXX THIS IS A PROTOTYPE XXX The wasm format is changing, and also this tool has not yet been fully tested
'''

import os, sys, shutil
from subprocess import Popen, PIPE, STDOUT

PYTHON = sys.executable

__rootpath__ = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
def path_from_root(*pathelems):
  return os.path.join(__rootpath__, *pathelems)

polyfill_dir = os.path.abspath(os.path.dirname(__file__))
def path_in_polyfill(*pathelems):
  return os.path.join(polyfill_dir, *pathelems)

jsfile = sys.argv[1]
wasmfile = sys.argv[2]

tempfile = jsfile + '.temp.js'
tempfile2 = jsfile + '.temp2.js'

print 'save the before js'
shutil.copyfile(jsfile, 'before.js')

print 'process input'
Popen([PYTHON, path_from_root('tools', 'distill_asm.py'), jsfile, tempfile]).communicate()
module = open(tempfile).read()
start = module.index('function')
end = module.rindex(')')
asm = module[start:end]
open(tempfile2, 'w').write(asm)

print 'run polyfill packer'
Popen([path_in_polyfill('tools', 'pack-asmjs'), tempfile2, wasmfile]).communicate()

print 'create patched out js'
js = open(jsfile).read()
patched = js.replace(asm, 'unwasmed') # we assume the module is right there
assert patched != js
patched = '''
function runEmscriptenModule(unwasmed) {

''' + patched + '''

}

''' + open(path_in_polyfill('jslib', 'load-wasm.js')).read() + '''

loadWebAssembly("''' + wasmfile + '''", 'load-wasm-worker.js').then(runEmscriptenModule);
'''
open(jsfile, 'w').write(patched)
shutil.copyfile(path_in_polyfill('jslib', 'load-wasm-worker.js'), 'load-wasm-worker.js')

