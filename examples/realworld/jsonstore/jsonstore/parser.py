import pyparsing as pp

# Parser for jsonstore filter expressions
def setTypeFieldname(toks):
    toks['token_type'] = 'fieldname'
    return toks

def setTypeValue(toks):
    toks['token_type'] = 'value'
    toks[0] = "'" + toks[0] + "'"
    return toks

lpar  = pp.Literal('(').suppress()
rpar  = pp.Literal(')').suppress()
fieldname = pp.Regex('[a-zA-Z_][a-zA-Z_0-9]*').setParseAction(setTypeFieldname)
operator = pp.Or([pp.Word('=<>', max=1), pp.Literal('<='), pp.Literal('>=')])
number = pp.Word(pp.nums)
string = pp.QuotedString("'", escChar='\\')
real = pp.Word(pp.nums + '.' + pp.nums)
value = pp.Or([number, string, real]).setParseAction(setTypeValue)
conjunction = pp.Or(['AND', 'OR'])
expression = pp.Forward()
comparison = pp.Group(fieldname) + operator + pp.Group(value) | pp.Group(lpar + expression + rpar)
expression << comparison + pp.ZeroOrMore(conjunction + expression)
grammar = pp.Or([pp.LineStart() + pp.LineEnd(), pp.LineStart() + expression + pp.LineEnd()])

def filter_exp_to_sql_where(filter_exp):
    filter_exp = filter_exp.strip()
    parse_tree = grammar.parseString(filter_exp)
    if len(parse_tree) == 0:
        return ''

    return parse_tree_to_sql_where(parse_tree)

def parse_tree_to_sql_where(parse_tree):
    def next_element():
        if len(parse_tree) > 0:
            return parse_tree.pop(0)

    where_clause = '('
    cur = next_element()

    while cur:
        if isinstance(cur, str):
            where_clause += str(cur)
            if len(parse_tree) > 0:
                where_clause += ' '
        else:
            if 'token_type' in cur and cur['token_type'] in ('fieldname', 'value'):
                if cur['token_type'] == 'fieldname':
                    where_clause += 'data->>\'' + str(cur[0]) + '\''
                else:
                    where_clause += str(cur[0])

                if len(parse_tree) > 0:
                    where_clause += ' '
            else:
                where_clause += parse_tree_to_sql_where(cur)
                if len(parse_tree) > 0:
                    where_clause += ' '

        cur = next_element()

    where_clause += ')'

    return where_clause
