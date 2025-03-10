import jedi
import sys
import json
import traceback
from rubicon.objc import at
from Foundation import NSAutoreleasePool, NSBundle
from pygments import highlight
from pygments import lexers
from pygments.formatters.terminal256 import TerminalTrueColorFormatter
from pygments.token import Keyword, Name, Comment, String, Number, Operator
from pygments.style import Style
from pyto import PyOutputHelper, ConsoleViewController, Python

_completions_queue = 0

lexer = lexers.get_lexer_by_name('python')

downloadable_path = str(NSBundle.mainBundle.pathForResource("Lib/_downloadable_packages", ofType=""))

def printHighlightedCode(code, _theme, path):

    theme = json.loads(_theme)

    style = type("CodeStyle", (Style,), { "styles": {
        Comment:                'italic '+theme["comment"],
        Keyword:                'bold '+theme["keyword"],
        Name:                   theme["name"],
        Name.Function:          theme["function"],
        Name.Class:             'bold '+theme["class"],
        String:                 theme["string"],
        Number:                 theme["number"],
        Operator:               theme["number"],
    }})
    formatter = TerminalTrueColorFormatter(full=True, style=style)
    PyOutputHelper.print(highlight(code, lexer, formatter), script=path)

def suggestForCode(code, index, path, get_definitions=False):
    global _completions_queue

    try:
        visibles = ConsoleViewController.objcVisibles
    except AttributeError:
        visibles = []

    if not downloadable_path in sys.path:
        sys.path.append(downloadable_path)

    for console in visibles:

        try:
            try:
                if console.editorSplitViewController is None:
                    continue
            except AttributeError:
                return

            try:
                visibleEditor = console.editorSplitViewController.editor
            except AttributeError:
                visibleEditor = console.editorSplitViewController().editor

            if visibleEditor is None:
                continue

            try:
                if visibleEditor.document.fileURL.path != path:
                    continue
            except AttributeError:
                if visibleEditor.document().fileURL.path != path:
                    continue

            if code.endswith(");\n"):
                if visibleEditor is None:
                    return

                visibleEditor.completions = []
                visibleEditor.suggestions = []
                visibleEditor.docStrings = None
                return
        except Exception as e:
            sys.__stdout__.write("Code completion:\n " + traceback.format_exc() + "\n")
            return

        try:
            script = jedi.Script(code, path=path)

            if get_definitions:
                definitions = []
                for _def in script.get_names():
                
                    if _def.type == "statement" or _def.type == "keyword":
                        continue
                
                    decl = _def.description
                    line = _def.line
                    if "=" in decl:
                        decl = decl.split("=")[0]
                    if ":" in decl:
                        decl = decl.split(":")[0]
                    
                    signatures = []
                    for signature in _def.get_signatures():
                        signatures.append(signature.to_string())
                    
                    defined_names = []
                    try:
                        for name in _def.defined_names():
                    
                            if not name.is_definition():
                                continue
                        
                            _signatures = []
                            for signature in name.get_signatures():
                                _signatures.append(signature.to_string())
                        
                            defined_names.append([name.description, name.line, name.docstring(raw=True), name.name, _signatures, [], name.module_name, name.type])
                    except NotImplementedError:
                        pass
                    
                    definitions.append([decl, line, _def.docstring(raw=True), _def.name, signatures, defined_names, _def.module_name, _def.type])

                visibleEditor.definitions = definitions

            suggestions = []
            completions = []

            docs = {}

            line = 1
            column = 0

            for i in range(index):
                char = code[i]
                if char == "\n":
                    line += 1
                    column = 0
                else:
                    column += 1

            signature = ""

            infer = script.infer(line, column)
            for _infer in infer:
                for __infer in _infer.get_signatures():
                    signature = __infer.to_string()
                    break
                break

            if signature == "":
                context = script.get_context(line, column)
                for _signature in context.get_signatures():
                    signature = _signature.to_string()
                    break

            _completions = script.complete(line, column)
            for completion in _completions:
                suggestion = completion.name

                if completion.complete.startswith("."):
                    suggestion = "." + suggestion

                complete = completion.complete
                if complete.endswith("="):
                    complete = complete[:-1]

                suggestions.append(suggestion)
                completions.append(complete)

                docs[suggestion] = ""

                if complete == "" and signature != "":
                    completions = []
                    suggestions = []
                    break
            
            if path.endswith(".py") and visibleEditor.text != code:
                return
            
            visibleEditor.lastCodeFromCompletions = code
            visibleEditor.signature = signature
            visibleEditor.completions = completions
            visibleEditor.suggestions = suggestions
            visibleEditor.docStrings = docs

        except Exception as e:

            sys.__stdout__.write("Code completion:\n " + traceback.format_exc() + "\n")

            if visibleEditor is None:
                return

            visibleEditor.completions = []
            visibleEditor.suggestions = []
            visibleEditor.signature = ""
            visibleEditor.docStrings = None

    if downloadable_path in sys.path:
        sys.path.remove(downloadable_path)

def suggestionsForCode(code, path=None):

    if not downloadable_path in sys.path:
        sys.path.append(downloadable_path)

    try:
        if path is None:
            script = jedi.Script(
                code, len(code.splitlines()), len(code.splitlines()[-1]) - 1
            )
        else:
            script = jedi.Script(
                code, len(code.splitlines()), len(code.splitlines()[-1]) - 1, path
            )

        suggestions = {}

        for completion in script.completions():

            if completion.complete.startswith("."):
                suggestion = "." + suggestion

            if completion.name.startswith("_"):
                continue

            suggestions[completion.name] = completion.complete

        if downloadable_path in sys.path:
            sys.path.remove(downloadable_path)

        return suggestions
    except Exception as e:
        if downloadable_path in sys.path:
            sys.path.remove(downloadable_path)

        return {}
