import re

# Classes for Prolog terms

class PObject(object):

    """ The Prolog object base class.
    This is intended as an abstract class.
    
    """
    
    # type tags
    inttype = 0
    floattype = 1
    vartype = 2
    stringtype = 3
    atomtype = 4
    listtype = 5
    structtype = 6

    def __init__(self):
        self.type = PObject.inttype
        self.val = 0
    
    def __str__(self):
        return str(self.val)

    def __eq__(self, t):
        return False
    
    def get_type(self):
        return self.type


class PInteger(PObject):
            
    """ Prolog integer subclass of PObject. """
    
    def __init__(self, v):
        """ v is the integer value of this object."""
        self.val = v
        self.type = PObject.inttype

    def __eq__(self, t):
        return t.type == PObject.inttype and self.val == t.val


class PFloat(PObject):
                
    """ Prolog float subclass of PObject. """
    
    def __init__(self, v):
        """ v is the float value of this object."""
        self.val = v
        self.type = PObject.floattype

    def __eq__(self, t):
        return t.type == PObject.floattype and self.val == t.val



class PVar(PObject):
                
    """ Prolog variable subclass of PObject. """
        
    def __init__(self,name):
        """ name is the name of this object."""
        self.val = name
        self.type = PObject.vartype

    def __eq__(self, t):
        return t.type == PObject.vartype and self.val == t.val



class PString(PObject):                

    """ Prolog string subclass of PObject. """      

    def __init__(self,chars, unescape=False):
        """ chars is the string value of this object."""
        if unescape:
            stripped_chars = chars[1:-1] # strip off the quotes
            # un-escape the string
            self.val = stripped_chars.encode('utf-8').decode('unicode-escape')
        else:
            self.val = chars
        self.type = PObject.stringtype

    def __str__(self):
        """ return the string representation - escape + escape " + add quotes. """
        return self.val
    
    def __eq__(self, t):
        return t.type == PObject.stringtype and str(self) == str(t)

class PAtom(PObject):

    """ Prolog atom subclass of PObject. """        

    @classmethod
    def atomize(cls, stringOrAtom):
        if stringOrAtom.__class__ == PAtom:
            return stringOrAtom
        else:
            return PAtom(stringOrAtom)
 
    def __init__(self,name):
        """ name is the name of this object."""
        self.val = name
        self.type = PObject.atomtype

    def __eq__(self, t):
        return t.type == PObject.atomtype and self.val == t.val


class PList(PObject):

    """ Prolog list subclass of PObject.

    Stored as a cons pair.

    """
    
    def __init__(self,h,t):
        """  h and t are the head an tail of the list."""
        self.head = h
        self.tail = t
        self.type = PObject.listtype

    def __str__(self):
        """ Display the Prolog list in standard Prolog form. """
        
        head = self.head
        tail = self.tail
        s = '[' + str(head)
        while tail.type == PObject.listtype:
            head = tail.head
            tail = tail.tail
            s += ', ' + str(head)
        if tail.val == '[]':
            s += ']'
        else:
            s += '|'+str(tail)+']'
        return s
            
    def toList(self):
        """ Return a Python list from the Prolog list

        return None if list does not end with a []
        """

        lst = []
        head = self.head
        tail = self.tail
        lst.append(head)
        while tail.type == PObject.listtype:
            head = tail.head
            tail = tail.tail
            lst.append(head)
        if tail.val == '[]':
            return lst
        else:
            return None
        
    def __eq__(self, t):
        if t.type != PObject.listtype:
            return False
        return self.head.__eq__(t.head) and self.tail.__eq__(t.tail)

class PStruct(PObject):

    """ Prolog structure subclass of PObject.

    Stored as the functor and a Python list of Prolog terms representing
    the arguments of the strudture.
    
    """
    def __init__(self,f,lst):
        """ f is the functor term and lst is the argument list. """
        self.functor = PAtom.atomize(f)
        self.args = lst
        self.type = PObject.structtype

    def arity(self):
        """ Return the arity of the structure. """
        return len(self.args)
    
    def __str__(self):
        """ Display the Prolog structure in standard Prolog form. """
        if self.args == []:
            # zero arity struct
            s = str(self.functor) + '()'
            return s
        s = str(self.functor) + '(' + str(self.args[0])
        for i in self.args[1:]:
            s = s + ', ' + str(i)
        s = s + ')'
        return s

    def __eq__(self, t):
        if t.type != PObject.structtype or not self.functor.__eq__(t.functor) or self.arity() != t.arity() :
            return False
        args = self.args
        t_args = t.args
        for i in range(self.arity()):
            if not args[i].__eq__(t_args[i]):
                return False
        return True
    
    

class ParseError(Exception):
    
    """ An exception object for parsing."""
    
    def __init__(self, pos):
        self.pos = pos

    def __str__(self):
        return repr(self.pos)


# A regular expression to distinguish between strings representing
# integers and floats
_floatRE = re.compile("[.eE]")

def _number_convert(x):
    """ Return the tagged token of the input string representing a number."""
    if (_floatRE.search(x)):
        return ('float', float(x))
    else:
        return ('int', int(x))

# A table of regular expressions that recognise tokens of various types
# and functions for conveting such strings into tagged tokens
_retable = (
    (  # for number tokens
    re.compile(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"),
    _number_convert
    ),
    (  # for the tokens ( ) [ ] ,
    re.compile(r"\(|\)|\[|\]|,|\|"),
    lambda x: ('sym', x)
    ),
    (  # for variable tokens
    re.compile(r"[_A-Z][A-Za-z0-9_]*"),
    lambda x: ('var', x)
    ),
    (  # for string tokens
    re.compile(r"\"[^\"\\]*(?:\\.[^\"\\]*)*\""),
    lambda x: ('string', x)
    ),
    (  # for atom tokens
    re.compile(r"[a-z][A-Za-z0-9_]*|'[^'\\]*(?:\\.[^'\\]*)*'|[-/+*<=>#@$\\^&~`:.?!;]+"),
    lambda x: ('atom', x)
    ),
    (  # catchall
    re.compile(r".*"),
    lambda x: ('eos', 'eos')
    )
)

# A regular expression used for consuming spaces in the parser
_spacesRE = re.compile('\s*')

class PedroParser:
    
    """A parser for Prolog terms used in Pedro.

    The method parse(string) returns a Prolog term (using Prolog term
    classes). An exception is thrown if the string does not parse.

    """
    def __init__(self):
        """ Set the string to be pased and the position in the string."""

        self.string = ''
        self.pos = 0

    def __next_token(self):
        """ Return the next tagged token from string at position pos. """
        end = _spacesRE.match(self.string).end()
        self.string = self.string[end:]
        self.pos += end
        for (regexp, fun) in _retable:
            m = regexp.match(self.string)
            if m:
                self.curr_token = fun(m.group(0))
                end = m.end()
                self.pos += end
                self.string = self.string[end:]
                break

    # return the list of terms representing structure argument
    def __parseargs(self):
        """ Return the list of prolog terms of an argument list."""

        t1 = [self.__prec700()]
        while (self.curr_token[1] == ','):
            self.__next_token()
            t2 = self.__prec700()
            t1.append(t2)
        return t1

    # return the list of terms representing list elements
    def __parselistargs(self):
        """ Return the list of prolog terms from a list."""
        t1 = self.__prec700()
        if (self.curr_token[1] == ','):
            self.__next_token()
            t2 = self.__parselistargs()
            return PList(t1, t2)
        elif self.curr_token[1] == '|':
            self.__next_token()
            t2 = self.__prec700()
            return PList(t1, t2)
        else:
            return PList(t1, PAtom('[]'))

    # parsing a basic term
    def __basic(self):
        """ Return a simple parsed term."""
        # nothing left - error
        if (self.curr_token[0] == 'eos'):
            raise ParseError(self.pos)
        # a string token 
        if (self.curr_token[0] == 'string'):
            t1 = PString(self.curr_token[1], True)
            self.__next_token()
            return t1
        # a var token
        if (self.curr_token[0] == 'var'):
            t1 = PVar(self.curr_token[1])
            self.__next_token()
            return t1
        # an int token
        if (self.curr_token[0] == 'int'):
            t1 = PInteger(self.curr_token[1])
            self.__next_token()
            return t1
        # a float token
        if (self.curr_token[0] == 'float'):
            t1 = PFloat(self.curr_token[1])
            self.__next_token()
            return t1
        # the start of a bracketed term
        # error if not terminated by a closing bracket
        if (self.curr_token[1] == '('):
            self.__next_token()
            t1 = self.__prec1100()
            if (self.curr_token[1] == ')'):
                self.__next_token()
                return t1
            raise ParseError(self.pos)
        # the start of a Prolog list
        # error if not terminated by ]
        if (self.curr_token[1] == '['):
            self.__next_token()
            if (self.curr_token[1] == ']'):
                self.__next_token()
                return PAtom('[]')
            t1 = self.__parselistargs()
            if (self.curr_token[1] == ']'):
                self.__next_token()
                return t1
            raise ParseError(self.pos)
        # at this point the current token is an atom token
        t1 = PAtom(self.curr_token[1])
        self.__next_token()
        if (self.curr_token[1] != '('):
            return t1
        # we have a structured term - e.g. f(a1, a2)
        self.__next_token()
        if (self.curr_token[1] == ')'):
            #  zeor arity struct
            t2 = PStruct(t1, [])
            self.__next_token()
            return t2
        t2 = self.__parseargs()
        if (self.curr_token[1] == ')'):
            self.__next_token()
            t2 = PStruct(t1, t2)
            return t2
        raise ParseError(self.pos)

    def __prec50(self):
        """ Parse a precedence 50 term. """
        
        t1 = self.__basic()
        if (self.curr_token[1] == ':'):
            op = PAtom(':')
            self.__next_token()
            t2 = self.__basic()
            t1 = PStruct(op, [t1, t2])
        return t1

    def __prec100(self):
        """ Parse a precedence 100 term. """
            
        t1 = self.__prec50()
        if (self.curr_token[1] == '@'):
            op = PAtom('@')
            self.__next_token()
            t2 = self.__prec50()
            t1 = PStruct(op, [t1, t2])
        return t1

    def __prec200(self):
        """ Parse a precedence 200 term. """
            
        if (self.curr_token[0] == 'eos'):
            raise ParseError(self.pos)
        if (self.curr_token[1] == '-'):
            self.__next_token()
            t2 = self.__prec100()
            # if we have - as a prefix operator followed by a number
            # then return the negated number
            if (t2.get_type() == PObject.inttype) or \
               (t2.get_type() == PObject.floattype):
                t2.val *= -1
                return t2
            op = PAtom('-')
            return PStruct(op, [t2])
        t1 = self.__prec100()
        if (self.curr_token[1] == '**'):
            op = PAtom('**')
            self.__next_token()
            t2 = self.__prec100()
            t1 = PStruct(op, [t1, t2])
        return t1

    def __prec400(self):
        """ Parse a precedence 400 term with left associative ops."""

        t1 = self.__prec200()   
        while (self.curr_token[1] in
            ('*', '/', '//', 'mod', '>>', '<<')):
            op = PAtom(self.curr_token[1])
            self.__next_token()
            t2 = self.__prec200()
            t1 = PStruct(op, [t1, t2])
        return t1

    def __prec500(self):
        """ Parse a precedence 500 term with left associative ops."""

        t1 = self.__prec400()   
        while (self.curr_token[1] in ('+','-', '\\/', '/\\')):
            op = PAtom(self.curr_token[1])
            self.__next_token()
            t2 = self.__prec400()
            t1 = PStruct(op, [t1, t2])
        return t1

    def __prec700(self):
        """ Parse a precedence 700 term."""

        t1 = self.__prec500()
        if (self.curr_token[1] in ('=', 'is', '<', '>', '=<', '>=')):
            op = PAtom(self.curr_token[1])
            self.__next_token()
            t2 = self.__prec500()
            t1 = PStruct(op, [t1, t2])
        return t1

    def __prec1000(self):
        """ Parse a precedence 1000 term."""

        t1 = self.__prec700()
        if (self.curr_token[1] == ','):
            op = PAtom(self.curr_token[1])
            self.__next_token()
            t2 = self.__prec1000()
            t1 = PStruct(op, [t1, t2])
        return t1

    def __prec1050(self):
        """ Parse a precedence 1050 term."""

        t1 = self.__prec1000()
        if (self.curr_token[1] == '->'):
            op = PAtom(self.curr_token[1])
            self.__next_token()
            t2 = self.__prec1050()
            t1 = PStruct(op, [t1, t2])
        return t1

    def __prec1100(self):
        """ Parse a precedence 1100 term."""

        t1 = self.__prec1050()
        if (self.curr_token[1] == ';'):
            op = PAtom(self.curr_token[1])
            self.__next_token()
            t2 = self.__prec1100()
            t1 = PStruct(op, [t1, t2])
        return t1

    def parse(self, str):
        """ Parse str into a Prolog term.

        An error is thrown if the string does not parse.

        """
        self.string = str
        self.pos = 0
        self.__next_token()
        try:
            t = self.__prec1100()
            if (self.curr_token[0] != 'eos'):
                raise ParseError(self.pos)
            return t
        except ParseError as e:
            print ("Parse error at position", e.pos)
            return None

