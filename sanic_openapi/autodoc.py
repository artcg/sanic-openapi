import yaml


class OpenAPIDocstringParser(object):
    def __init__(self, docstring):
        ''' docstring should be parsed via inspect.getdoc '''
        self.docstring = docstring

    def to_openAPI_2(self):
        raise NotImplementedError()

    def to_openAPI_3(self):
        raise NotImplementedError()


# similar -- https://github.com/flasgger/flasgger/blob/master/flasgger/utils.py
class YamlStyleParametersParser(OpenAPIDocstringParser):
    def to_openAPI_2(self):
        import pdb
        pdb.set_trace()
        if '---' in self.docstring:
            doc, conf = self.docstring.split('---', 1)
            conf = yaml.safe_load(conf)
        else:
            doc = self.docstring
            conf = {}
        if doc.count('\n') > 1:
            conf["summary"], conf["description"] = doc.split('\n', 1)
        else:
            conf["summary"] = doc


class GoogleStyleParametersParser(OpenAPIDocstringParser):
    '''
    Not-quite-google-style

    detects a section called "QueryParameters:", and expects entries of the form

    param_name (param_type [, required] [, default=default_val]):
        description
    '''
    def tree(self, lines):
        lines = [line for line in lines if line.strip()]
        indents = [len(line) - len(line.lstrip()) for line in lines]
        node_idxs = [n for n, i in enumerate(indents) if i == min(indents)]

        if len(node_idxs) == len(lines):
            return lines
        assert 0 in node_idxs
        tree = {}
        for prev, current in zip(node_idxs, node_idxs[1:] + [len(lines)]):
            # tree[(prev, lines[prev])] = self.tree(lines[prev + 1:current])
            tree[lines[prev]] = self.tree(lines[prev + 1:current])

        return tree

    def parse_parameter_line(self, line):
        import pdb; pdb.set_trace()
        assert line.count('(') == 1
        assert line.count(')') == 1
        assert line.count(':') == 1 and line.endswith('):')
        param_name, line = line.split('(')
        param_name = param_name.strip()

        param_type, line = line.split(')')
        param_type, *param_type_kwargs = param_type.split(',')
        param_type = param_type.strip()

        assert param_type in ("str", "int")

        required = False
        default = None
        for kwarg in param_type_kwargs:
            kwarg = kwarg.strip()
            if kwarg == 'required':
                required = True
            elif kwarg.startswith('default'):
                assert kwarg.count('=') == 1
                default = kwarg.split('=')[1].strip()

        return {"name": param_name, "type": param_type,
                "required": required, "default": default}

    def match(self):
        tree = self.tree(self.docstring.split('\n'))
        return [self.parse_parameter_line(line)
                for line in tree['QueryParameters:'].keys()]
