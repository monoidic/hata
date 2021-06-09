__all__ = ('EvaluationError', 'evaluate_text', )

import math

from ...backend.utils import copy_docs

from .exceptions import SlashCommandError

LIMIT_LEFT_SHIFT_MAX = 64*8
LIMIT_RIGHT_SHIFT_MIN = -64*8
LIMIT_POWER_MAX = 64
LIMIT_INTEGER_BIT_LENGTH = 64*32
LIMIT_INTEGER_MAX = 1<<LIMIT_INTEGER_BIT_LENGTH
LIMIT_INTEGER_MIN = -LIMIT_INTEGER_MAX
LIMIT_FACTORIAL_MAX = 80

STATIC_NONE_ID = 0

OPERATION_ADD_ID = 1
OPERATION_ADD_STRING = '+'

OPERATION_BINARY_AND_ID = 2
OPERATION_BINARY_AND_STRING = '&'

OPERATION_NEGATE_ID = 3
OPERATION_NEGATE_STRING = '-'

OPERATION_SUBTRACTION_ID = 4
OPERATION_SUBTRACTION_STRING = '-'

OPERATION_INVERT_ID = 5
OPERATION_INVERT_STRING = '~'

OPERATION_LEFT_SHIFT_ID = 6
OPERATION_LEFT_SHIFT_STRING = '<<'

OPERATION_RIGHT_SHIFT_ID = 7
OPERATION_RIGHT_SHIFT_STRING = '>>'

OPERATION_BINARY_OR_ID = 8
OPERATION_BINARY_OR_STRING = '|'

OPERATION_BINARY_XOR_ID = 9
OPERATION_BINARY_XOR_STRING = '^'

OPERATION_PARENTHESES_START_ID = 10
OPERATION_PARENTHESES_START_STRING = '('

OPERATION_PARENTHESES_END_ID = 11
OPERATION_PARENTHESES_END_STRING = ')'

OPERATION_REMAINDER_ID = 12
OPERATION_REMAINDERS_STRING = '%'

OPERATION_TRUE_DIVISION_ID = 13
OPERATION_TRUE_DIVISION_STRING = '/'

OPERATION_FULL_DIVISION_ID = 14
OPERATION_FULL_DIVISION_STRING = '//'

OPERATION_POSITIVATE_ID = 15
OPERATION_POSITIVATE_STRING = '+'

OPERATION_MULTIPLY_ID = 16
OPERATION_MULTIPLY_STRING = '*'

OPERATION_POWER_ID = 27
OPERATION_POWER_STRING = '**'

STATIC_NUMERIC_DECIMAL_ID = 17
STATIC_NUMERIC_HEXADECIMAL_ID = 18
STATIC_NUMERIC_OCTAL_ID = 19
STATIC_NUMERIC_BINARY_ID = 20
STATIC_NUMERIC_FLOAT_ID = 24
VARIABLE_EVALUATED = 23

VARIABLE_IDENTIFIER = 21

TOKEN_GROUP_PARENTHESES = 22
TOKEN_GROUP_FUNCTION_CALL = 26

VARIABLE_FUNCTION = 25

# Last id is 27


NUMERIC_POSTFIX_MULTIPLIERS = {
    b'k'[0]: 1_000,
    b'K'[0]: 1_000,
    b'm'[0]: 1_000_000,
    b'M'[0]: 1_000_000,
    b'g'[0]: 1_000_000_000,
    b'G'[0]: 1_000_000_000,
    b't'[0]: 1_000_000_000_000,
    b'T'[0]: 1_000_000_000_000,
}

SPACE_CHARACTERS = frozenset((
    ' ',
    '\t',
))


OPERATION_CHARACTERS = frozenset((
    *OPERATION_ADD_STRING,
    *OPERATION_BINARY_AND_STRING,
    *OPERATION_NEGATE_STRING,
    *OPERATION_SUBTRACTION_STRING,
    *OPERATION_INVERT_STRING,
    *OPERATION_LEFT_SHIFT_STRING,
    *OPERATION_RIGHT_SHIFT_STRING,
    *OPERATION_BINARY_OR_STRING,
    *OPERATION_BINARY_XOR_STRING,
    *OPERATION_PARENTHESES_START_STRING,
    *OPERATION_PARENTHESES_END_STRING,
    *OPERATION_REMAINDERS_STRING,
    *OPERATION_TRUE_DIVISION_STRING,
    *OPERATION_FULL_DIVISION_STRING,
    *OPERATION_POSITIVATE_STRING,
    *OPERATION_MULTIPLY_STRING,
))

TOKEN_NAMES = {
    OPERATION_ADD_ID: 'add',
    OPERATION_BINARY_AND_ID : 'binary and',
    OPERATION_NEGATE_ID: 'negate',
    OPERATION_SUBTRACTION_ID: 'subtraction',
    OPERATION_INVERT_ID: 'invert',
    OPERATION_LEFT_SHIFT_ID: 'left shift',
    OPERATION_RIGHT_SHIFT_ID: 'right shift',
    OPERATION_BINARY_OR_ID: 'binary or',
    OPERATION_BINARY_XOR_ID: 'binary xor',
    OPERATION_PARENTHESES_START_ID: 'parentheses start',
    OPERATION_PARENTHESES_END_ID: 'parentheses end',
    OPERATION_REMAINDER_ID: 'remainder',
    OPERATION_TRUE_DIVISION_ID: 'true division',
    OPERATION_FULL_DIVISION_ID: 'full division',
    OPERATION_POSITIVATE_ID: 'positivate',
    OPERATION_MULTIPLY_ID: 'multiply',
    STATIC_NUMERIC_DECIMAL_ID: 'decimal integer',
    STATIC_NUMERIC_HEXADECIMAL_ID: 'hexadecimal integer',
    STATIC_NUMERIC_OCTAL_ID: 'octal integer',
    STATIC_NUMERIC_BINARY_ID: 'binary integer',
    STATIC_NUMERIC_FLOAT_ID: 'float',
    VARIABLE_IDENTIFIER: 'identifier',
    VARIABLE_EVALUATED: 'variable',
    VARIABLE_FUNCTION: 'function',
    TOKEN_GROUP_PARENTHESES: 'parentheses',
    TOKEN_GROUP_FUNCTION_CALL : 'function call',
}

TWO_SIDE_OPERATORS = frozenset((
    OPERATION_BINARY_AND_ID,
    OPERATION_LEFT_SHIFT_ID,
    OPERATION_RIGHT_SHIFT_ID,
    OPERATION_BINARY_OR_ID,
    OPERATION_BINARY_XOR_ID,
    OPERATION_REMAINDER_ID,
    OPERATION_TRUE_DIVISION_ID,
    OPERATION_FULL_DIVISION_ID,
    OPERATION_MULTIPLY_ID,
))

TWO_SIDE_OPERATORS_AND_PARENTHESES_END = frozenset((
    *TWO_SIDE_OPERATORS,
    OPERATION_PARENTHESES_END_ID,
))

PREFIX_OPERATORS = frozenset((
    OPERATION_ADD_ID,
    OPERATION_NEGATE_ID,
    OPERATION_SUBTRACTION_ID,
    OPERATION_POSITIVATE_ID,
    OPERATION_INVERT_ID,
))

CANT_FOLLOW_VARIABLE = frozenset((
    STATIC_NUMERIC_DECIMAL_ID,
    STATIC_NUMERIC_HEXADECIMAL_ID,
    STATIC_NUMERIC_OCTAL_ID,
    STATIC_NUMERIC_BINARY_ID,
    VARIABLE_IDENTIFIER,
    STATIC_NUMERIC_FLOAT_ID,
    OPERATION_PARENTHESES_START_ID,
    OPERATION_INVERT_ID,
    VARIABLE_FUNCTION,
))

CANT_FOLLOW_FUNCTION = frozenset((
    STATIC_NUMERIC_DECIMAL_ID,
    STATIC_NUMERIC_HEXADECIMAL_ID,
    STATIC_NUMERIC_OCTAL_ID,
    STATIC_NUMERIC_BINARY_ID,
    VARIABLE_IDENTIFIER,
    OPERATION_PARENTHESES_END_ID,
    *TWO_SIDE_OPERATORS,
    *PREFIX_OPERATORS,
    VARIABLE_FUNCTION,
))

CANT_START = frozenset((
    *TWO_SIDE_OPERATORS,
    OPERATION_PARENTHESES_END_ID,
))

CANT_FOLLOW = {
    OPERATION_BINARY_AND_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_INVERT_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_LEFT_SHIFT_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_RIGHT_SHIFT_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_BINARY_OR_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_BINARY_XOR_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_REMAINDER_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_TRUE_DIVISION_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_FULL_DIVISION_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_MULTIPLY_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    
    OPERATION_ADD_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_NEGATE_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_SUBTRACTION_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    OPERATION_POSITIVATE_ID: TWO_SIDE_OPERATORS_AND_PARENTHESES_END,
    
    STATIC_NUMERIC_DECIMAL_ID: CANT_FOLLOW_VARIABLE,
    STATIC_NUMERIC_HEXADECIMAL_ID: CANT_FOLLOW_VARIABLE,
    STATIC_NUMERIC_OCTAL_ID: CANT_FOLLOW_VARIABLE,
    STATIC_NUMERIC_BINARY_ID: CANT_FOLLOW_VARIABLE,
    VARIABLE_EVALUATED: CANT_FOLLOW_VARIABLE,
    STATIC_NUMERIC_FLOAT_ID: CANT_FOLLOW_VARIABLE,
    VARIABLE_FUNCTION: CANT_FOLLOW_FUNCTION,
    OPERATION_PARENTHESES_START_ID: frozenset((OPERATION_PARENTHESES_END_ID,)),
    OPERATION_PARENTHESES_END_ID: CANT_FOLLOW_VARIABLE,

}

CANT_END = frozenset((
    *PREFIX_OPERATORS,
    *TWO_SIDE_OPERATORS,
    OPERATION_INVERT_ID,
    OPERATION_PARENTHESES_START_ID,
    VARIABLE_FUNCTION,
))


OPERATORS = frozenset((
    OPERATION_ADD_ID,
    OPERATION_BINARY_AND_ID,
    OPERATION_NEGATE_ID,
    OPERATION_SUBTRACTION_ID,
    OPERATION_INVERT_ID,
    OPERATION_LEFT_SHIFT_ID,
    OPERATION_RIGHT_SHIFT_ID,
    OPERATION_BINARY_OR_STRING,
    OPERATION_BINARY_XOR_STRING,
    OPERATION_REMAINDERS_STRING,
    OPERATION_TRUE_DIVISION_STRING,
    OPERATION_FULL_DIVISION_STRING,
    OPERATION_POSITIVATE_STRING,
    OPERATION_MULTIPLY_STRING,
))


VARIABLES = frozenset((
    STATIC_NUMERIC_DECIMAL_ID,
    STATIC_NUMERIC_HEXADECIMAL_ID,
    STATIC_NUMERIC_OCTAL_ID,
    STATIC_NUMERIC_BINARY_ID,
    VARIABLE_EVALUATED,
))

OPERATION_TWO_SIDED_BINARY = frozenset((
    OPERATION_BINARY_AND_STRING,
    OPERATION_LEFT_SHIFT_ID,
    OPERATION_RIGHT_SHIFT_ID,
    OPERATION_BINARY_OR_ID,
    OPERATION_BINARY_XOR_ID,
))




def get_numeric_postfix_multiplier(raw_value):
    """
    Gets numeric postfix multiplier.
    
    Parameters
    ----------
    raw_value : `tuple` of `int`
        The value to get the multiplier off.
    
    Returns
    -------
    value : `bytes`
        The value without the multiplier.
    total_multiplier : `int`
        Multiplier to multiply the value with,
    """
    limit = len(raw_value)-1
    index = limit
    
    total_multiplier = 1
    while True:
        postfix = raw_value[index]
        try:
            multiplier = NUMERIC_POSTFIX_MULTIPLIERS[postfix]
        except KeyError:
            break
        
        total_multiplier *= multiplier
    
    if index != limit:
        raw_value = raw_value[:index+1]
    
    return raw_value, total_multiplier


def evaluate_numeric_float(raw_value):
    """
    Evaluates the given numeric decimal value.
    
    Parameter
    ---------
    raw_value : `tuple` of `int`
        The value to evaluate.
    
    Returns
    -------
    raw_value : `int`
        The evaluated value.
    token_id : `int`
        The token's new identifier.
    """
    raw_value = bytes(raw_value)
    value = float(raw_value)
    return value, STATIC_NUMERIC_FLOAT_ID


def evaluate_numeric_decimal(raw_value):
    """
    Evaluates the given numeric decimal value.
    
    Parameter
    ---------
    raw_value : `tuple` of `int`
        The value to evaluate.
    
    Returns
    -------
    value : `int`
        The evaluated value.
    token_id : `int`
        The token's new identifier.
    """
    raw_value, multiplier = get_numeric_postfix_multiplier(raw_value)
    raw_value = bytes(raw_value)
    value = int(raw_value)*multiplier
    return value, STATIC_NUMERIC_DECIMAL_ID


def evaluate_numeric_hexadecimal(raw_value):
    """
    Evaluates the given numeric hexadecimal value.
    
    Parameter
    ---------
    raw_value : `tuple` of `int`
        The value to evaluate.
    
    Returns
    -------
    value : `int`
        The evaluated value.
    token_id : `int`
        The token's new identifier.
    """
    raw_value = bytes(raw_value)
    value = int(raw_value, base=16)
    return value, STATIC_NUMERIC_HEXADECIMAL_ID


def evaluate_numeric_octal(raw_value):
    """
    Evaluates the given numeric octal value.
    
    Parameter
    ---------
    raw_value : `tuple` of `int`
        The value to evaluate.
    
    Returns
    -------
    value : `int`
        The evaluated value.
    token_id : `int`
        The token's new identifier.
    """
    raw_value = bytes(raw_value)
    value = int(raw_value, base=8)
    return value, STATIC_NUMERIC_OCTAL_ID

def evaluate_numeric_binary(raw_value):
    """
    Evaluates the given numeric binary value.
    
    Parameter
    ---------
    raw_value : `tuple` of `int`
        The value to evaluate.
    
    Returns
    -------
    value : `int`
        The evaluated value.
    token_id : `int`
        The token's new identifier.
    """
    raw_value = bytes(raw_value)
    value = int(raw_value, base=2)
    return value, STATIC_NUMERIC_BINARY_ID


def check_factorial_validity(token, value):
    """
    Checks whether the factorial call is in limit.
    
    Parameters
    ----------
    token : ``Token``
        The parent token.
    value : `int` or `float`
        The value to use factorial on.
    
    Raises
    ------
    EvaluationError
        - Factorial is only allowed for integral values.
        - Factorial nto defined for negative values.
        - Operation over factorial limit is disallowed.
    """
    if (not isinstance(value, int)) and (not value.is_integer()):
        raise EvaluationError(
            token.array, token.start, token.end,
            f'Factorial only accepts integral values: factorial({value!r})',
        )
    
    if value < 0:
        raise EvaluationError(
            token.array, token.start, token.end,
            f'Factorial is not defined for negative values: factorial({value!r})',
        )
    
    if value > LIMIT_FACTORIAL_MAX:
        raise EvaluationError(
            token.array, token.start, token.end,
            f'Factorial over {LIMIT_INTEGER_BIT_LENGTH} is disallowed: factorial({value!r})',
        )


STATIC_VARIABLE_TABLE = {
    b'e': math.e,
    b'pi': math.pi,
    b'tau': math.tau,
}

STATIC_FUNCTION_TABLE = {
    b'abs': (abs, None),
    b'acos': (math.acos, None),
    b'acosh': (math.acosh, None),
    b'asin': (math.asin, None),
    b'asinh': (math.asinh, None),
    b'atan': (math.atan, None),
    b'atanh': (math.atanh, None),
    b'ceil': (math.ceil, None),
    b'cos': (math.cos, None),
    b'cosh': (math.cosh, None),
    b'degrees': (math.degrees, None),
    b'erf': (math.erf, None),
    b'erfc': (math.erfc, None),
    b'exp': (math.exp, None),
    b'expm1': (math.expm1, None),
    b'fabs': (math.fabs, None),
    b'factorial': (math.factorial, check_factorial_validity),
    b'floor': (math.floor, None),
    b'log': (math.log, None),
    b'log10': (math.log10, None),
    b'log1p': (math.log1p, None),
    b'log2': (math.log2, None),
    b'modf': (math.modf, None),
    b'radians': (math.radians, None),
    b'round': (round, None),
    b'sin': (math.sin, None),
    b'sinh': (math.sinh, None),
    b'sqrt': (math.sqrt, None),
    b'tan': (math.tan, None),
}

def evaluate_identifier(raw_value):
    """
    Evaluates the given identifier token.
    
    Parameter
    ---------
    raw_value : `tuple` of `int`
        The value to evaluate.
    
    Returns
    -------
    value : `float`, `FunctionType`
        The evaluated value.
    token_id : `int`
        The token's new identifier.
    """
    raw_value = bytes(raw_value)
    raw_value = raw_value.lower()
    
    while True:
        try:
            value = STATIC_VARIABLE_TABLE[raw_value]
        except KeyError:
            pass
        else:
            token_id = VARIABLE_EVALUATED
            break
        
        try:
            value = STATIC_FUNCTION_TABLE[raw_value]
        except KeyError:
            pass
        else:
            token_id = VARIABLE_FUNCTION
            break
        
        value = None
        token_id = STATIC_NONE_ID
        break
    
    return value, token_id


EVALUATORS = {
    STATIC_NUMERIC_FLOAT_ID: evaluate_numeric_float,
    STATIC_NUMERIC_DECIMAL_ID: evaluate_numeric_decimal,
    STATIC_NUMERIC_HEXADECIMAL_ID: evaluate_numeric_hexadecimal,
    STATIC_NUMERIC_OCTAL_ID: evaluate_numeric_octal,
    STATIC_NUMERIC_BINARY_ID: evaluate_numeric_binary,
    VARIABLE_IDENTIFIER: evaluate_identifier,
}


OPERATION_PREFIXABLE = frozenset((
    OPERATION_ADD_ID,
    OPERATION_NEGATE_ID,
    OPERATION_SUBTRACTION_ID,
    OPERATION_INVERT_ID,
    OPERATION_POSITIVATE_ID,
))

CAN_EXECUTE_PREFIX_PATTERN_1 = frozenset((
    STATIC_NONE_ID,
    *OPERATION_PREFIXABLE,
    *TWO_SIDE_OPERATORS,
))

CAN_EXECUTE_PREFIX_PATTERN_2 = OPERATION_PREFIXABLE

CAN_EXECUTE_PREFIX_PATTERN_3 = frozenset((
    *VARIABLES,
    VARIABLE_EVALUATED,
))


def merge_2_tokens(token_1, token_2, value):
    """
    Merges the given two token with a new value.
    
    Parameters
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token.
    value : `Any`
        The value to add to the created token.
    
    Returns
    -------
    token : ``Token``
        The created token.
    """
    return Token(token_1.array, token_1.start, token_2.end, VARIABLE_EVALUATED, None, value)


def check_2_sided_integer_limit(token_1, token_2, token_3):
    """
    Checks whether the integer value passes the limit.
    
    Parameters
    ----------
    token_1 : ``Token``
        The first value to check.
    token_2 :  ``Token``
        The operation's token.
    token_3 : ``Token``
        The first value to check.
    
    Raises
    ------
    EvaluationError
        Operation over integer bit limit is disallowed.
    """
    value_1 = token_1.value
    value_2 = token_3.value
    if isinstance(value_1, int) and isinstance(value_2, int):
        if (value_1 >= LIMIT_INTEGER_MAX) or (value_1 <= LIMIT_INTEGER_MIN):
            raise EvaluationError(
                token_2.array, token_1.start, token_2.end,
                f'Integer operation over {LIMIT_INTEGER_BIT_LENGTH} bit limit is disallowed.',
            )
        
        if (value_2 >= LIMIT_INTEGER_MAX) or (value_2 <= LIMIT_INTEGER_MIN):
            raise EvaluationError(
                token_2.array, token_2.start, token_3.end,
                f'Integer operation over {LIMIT_INTEGER_BIT_LENGTH} bit limit is disallowed.',
            )


def evaluate_prefix_operation_negate(token_1, token_2):
    """
    Evaluate negation on the given value.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    """
    value = -token_2.value
    return merge_2_tokens(token_1, token_2, value)


def evaluate_prefix_operation_positivate(token_1, token_2):
    """
    Evaluate positivate on the given value.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    """
    value = +token_2.value
    return merge_2_tokens(token_1, token_2, value)


def evaluate_prefix_operation_invert(token_1, token_2):
    """
    Evaluate revert on the given value.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    """
    value = ~token_2.value
    return merge_2_tokens(token_1, token_2, value)


EVALUATE_1_SIDED_OPERATION = {
    OPERATION_ADD_ID: evaluate_prefix_operation_positivate,
    OPERATION_NEGATE_ID: evaluate_prefix_operation_negate,
    OPERATION_SUBTRACTION_ID: evaluate_prefix_operation_negate,
    OPERATION_INVERT_ID: evaluate_prefix_operation_invert,
    OPERATION_POSITIVATE_ID: evaluate_prefix_operation_positivate,
}


CAN_EXECUTE_POWER = frozenset((
    OPERATION_POWER_ID,
))

CAN_EXECUTE_MULTIPLICATION_PATTERN_MIDDLE = frozenset((
    OPERATION_TRUE_DIVISION_ID,
    OPERATION_FULL_DIVISION_ID,
    OPERATION_MULTIPLY_ID,
    OPERATION_REMAINDER_ID,
))

CAN_EXECUTE_ADDITION_PATTERN_MIDDLE = frozenset((
    OPERATION_ADD_ID,
    OPERATION_SUBTRACTION_ID,
))

CAN_EXECUTE_SHIFT_PATTERN_MIDDLE = frozenset((
    OPERATION_LEFT_SHIFT_ID,
    OPERATION_RIGHT_SHIFT_ID,
))


CAN_EXECUTE_BINARY_AND_PATTERN_MIDDLE = frozenset((
    OPERATION_BINARY_AND_ID,
))


CAN_EXECUTE_BINARY_XOR_MIDDLE = frozenset((
    OPERATION_BINARY_XOR_ID,
))


CAN_EXECUTE_BINARY_OR_MIDDLE = frozenset((
    OPERATION_BINARY_OR_ID,
))


CAN_EXECUTE_TWO_SIDED_ORDERED = (
    CAN_EXECUTE_POWER,
    CAN_EXECUTE_MULTIPLICATION_PATTERN_MIDDLE,
    CAN_EXECUTE_ADDITION_PATTERN_MIDDLE,
    CAN_EXECUTE_SHIFT_PATTERN_MIDDLE,
    CAN_EXECUTE_BINARY_AND_PATTERN_MIDDLE,
    CAN_EXECUTE_BINARY_XOR_MIDDLE,
    CAN_EXECUTE_BINARY_OR_MIDDLE,
)


def evaluate_2_sided_true_division(token_1, token_2, token_3):
    """
    Evaluates true division on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    
    Raises
    ------
    EvaluationError
        - Division by zero disallowed.
        - Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value_1 = token_1.value
    value_2 = token_3.value
    if value_2 == 0:
        raise EvaluationError(token_2.array, token_2.start, token_2.end,
            f'True division by zero disallowed: {value_1} / {value_2}.')
    
    value = value_1 / value_2
    return merge_2_tokens(token_1, token_3, value)


def evaluate_2_sided_full_division(token_1, token_2, token_3):
    """
    Evaluates full division on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    
    Raises
    ------
    EvaluationError
        - Division by zero disallowed.
        - Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value_1 = token_1.value
    value_2 = token_3.value
    if value_2 == 0:
        raise EvaluationError(token_2.array, token_2.start, token_2.end,
            f'Full division by zero disallowed: {value_1} // {value_2}.')
    
    value = value_1 // value_2
    return merge_2_tokens(token_1, token_3, value)


def evaluate_2_sided_multiply(token_1, token_2, token_3):
    """
    Evaluates full division on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    
    Raises
    ------
    EvaluationError
        Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value = token_1.value * token_3.value
    return merge_2_tokens(token_1, token_3, value)


def evaluate_2_sided_remainder(token_1, token_2, token_3):
    """
    Evaluates remainder on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    
    Raises
    ------
    EvaluationError
        - Remainder by zero disallowed.
        - Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value_1 = token_1.value
    value_2 = token_3.value
    if value_2 == 0:
        raise EvaluationError(token_2.array, token_2.start, token_2.end,
            f'Remainder by zero disallowed: {value_1} % {value_2}.')
    
    value = value_1 // value_2
    return merge_2_tokens(token_1, token_3, value)


def evaluate_2_sided_add(token_1, token_2, token_3):
    """
    Evaluates add on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    
    Raises
    ------
    EvaluationError
        - Remainder by zero disallowed.
        - Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value = token_1.value + token_3.value
    return merge_2_tokens(token_1, token_3, value)


def evaluate_2_sided_subtraction(token_1, token_2, token_3):
    """
    Evaluates subtraction on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    
    Raises
    ------
    EvaluationError
        Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value = token_1.value - token_3.value
    return merge_2_tokens(token_1, token_3, value)


def evaluate_2_sided_binary_left_shift(token_1, token_2, token_3):
    """
    Evaluates left shift on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    
    Raises
    ------
    EvaluationError
        - Left shift limit hit.
        - Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value_1 = token_1.value
    value_2 = token_3.value
    if value_2 > LIMIT_LEFT_SHIFT_MAX:
        raise EvaluationError(token_2.array, token_2.start, token_2.end,
            f'Left shift over {LIMIT_LEFT_SHIFT_MAX} disallowed: {value_1} << {value_2}.')
    
    value = token_1.value << token_3.value
    return merge_2_tokens(token_1, token_3, value)


def evaluate_2_sided_binary_right_shift(token_1, token_2, token_3):
    """
    Evaluates right shift on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    
    Raises
    ------
    EvaluationError
        - Left shift limit hit.
        - Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value_1 = token_1.value
    value_2 = token_3.value
    if value_2 < LIMIT_RIGHT_SHIFT_MIN:
        raise EvaluationError(token_2.array, token_2.start, token_2.end,
            f'Left shift under {LIMIT_RIGHT_SHIFT_MIN} disallowed: {value_1} >> {value_2}.')
    
    value = token_1.value >> token_3.value
    return merge_2_tokens(token_1, token_3, value)


def evaluate_2_sided_binary_and(token_1, token_2, token_3):
    """
    Evaluates binary and on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        - The created token.
        - Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value = token_1.value & token_3.value
    return merge_2_tokens(token_1, token_3, value)


def evaluate_2_sided_binary_xor(token_1, token_2, token_3):
    """
    Evaluates binary xor on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        - The created token.
        - Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value = token_1.value ^ token_3.value
    return merge_2_tokens(token_1, token_3, value)


def evaluate_2_sided_binary_or(token_1, token_2, token_3):
    """
    Evaluates binary and on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        - The created token.
        - Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value = token_1.value | token_3.value
    return merge_2_tokens(token_1, token_3, value)


def evaluate_2_sided_power(token_1, token_2, token_3):
    """
    Evaluates power on the given values.
    
    Attributes
    ----------
    token_1 : ``Token``
        The first token.
    token_2 : ``Token``
        The second token with the value.
    token_3 : ``Token``
        The third token with the value.
    
    Returns
    -------
    token : ``Token``
        The created token.
    
    Raises
    ------
    EvaluationError
        - Power limit hit.
        - Operation over integer bit limit is disallowed.
    """
    check_2_sided_integer_limit(token_1, token_2, token_3)
    
    value_1 = token_1.value
    value_2 = token_3.value
    if value_2 > LIMIT_POWER_MAX:
        raise EvaluationError(
            token_2.array, token_2.start, token_3.end,
            f'Power over {LIMIT_POWER_MAX} disallowed: {value_1} ** {value_2}.'
        )
    
    if value_1.bit_length()*value_2.bit_length() > LIMIT_INTEGER_BIT_LENGTH:
        raise EvaluationError(
            token_1.array, token_1.start, token_3.end,
            f'Power over possible {LIMIT_INTEGER_BIT_LENGTH} bit length disallowed: {value_1} ** {value_2}.'
        )
    
    value = token_1.value ** token_3.value
    return merge_2_tokens(token_1, token_3, value)


EVALUATE_2_SIDED_OPERATION = {
    OPERATION_TRUE_DIVISION_ID: evaluate_2_sided_true_division,
    OPERATION_FULL_DIVISION_ID: evaluate_2_sided_full_division,
    OPERATION_MULTIPLY_ID: evaluate_2_sided_multiply,
    OPERATION_REMAINDER_ID: evaluate_2_sided_remainder,
    OPERATION_ADD_ID: evaluate_2_sided_add,
    OPERATION_SUBTRACTION_ID: evaluate_2_sided_subtraction,
    OPERATION_LEFT_SHIFT_ID: evaluate_2_sided_binary_left_shift,
    OPERATION_RIGHT_SHIFT_ID: evaluate_2_sided_binary_right_shift,
    OPERATION_BINARY_AND_ID: evaluate_2_sided_binary_and,
    OPERATION_BINARY_XOR_ID: evaluate_2_sided_binary_xor,
    OPERATION_BINARY_OR_ID: evaluate_2_sided_binary_or,
    OPERATION_POWER_ID: evaluate_2_sided_power,
}


class ParserBase:
    """
    Base class for parser instances.
    """
    __slots__ = ()
    def __new__(cls):
        """
        Creates a new parser instance.
        """
        self = object.__new__(cls)
        return self
    
    def __call__(self, state):
        """
        Calls the parser returning whether it succeeded.
        
        Parameters
        ----------
        state : ``ParsingState``
            Parsing state to track the details of the actual parsing.
        
        Returns
        -------
        success : `bool`
        
        Raises
        ------
        EvaluationError
            Any syntax error occurred.
        """
        return False
    
    def __repr__(self):
        """Returns the parser's representation."""
        return f'{self.__class__.__name__}()'


class ParserIdentifier(ParserBase):
    """
    Parser to add tokens to the parsing state.
    
    Attributes
    ----------
    id : `int`
        When parsing success, add a new token to the state.
    """
    __slots__ = ('id', 'parser',)
    def __new__(cls, parser, identifier):
        """
        Creates a new ``ParserIdentifier`` from the given parameters.
        
        Parameters
        ----------
        parser : ``ParserBase``
            The parser to match.
        identifier : `int`
            When parsing success, add a new token to the state.
        """
        self = object.__new__(cls)
        self.parser = parser
        self.id = identifier
        return self
    
    @copy_docs(ParserBase.__call__)
    def __call__(self, state):
        index = state.index
        if index == state.end:
            return True
        
        if self.parser(state):
            state.add_token(index, self.id)
            return True
        
        return False
    
    @copy_docs(ParserBase.__repr__)
    def __repr__(self):
        return f'{self.__class__.__name__}({self.parser!r}, {self.id!r})'


class ParserPostfixCheck(ParserBase):
    """
    Checks postfix after an other pattern.
    
    Attributes
    ----------
    parser : ``ParserBase``
        The postfix parser to check.
    message : `str`
        Message of the error.
    """
    __slots__ = ('parser', 'message')
    def __new__(cls, parser, message):
        """
        Creates a new ``ParserPostfixCheck`` instance.
        
        Parameters
        ----------
        parser : ``ParserBase``
            The postfix parser to check.
        message : `str`
            Message of the error.
        """
        self = object.__new__(cls)
        self.parser = parser
        self.message = message
        return self
    
    @copy_docs(ParserBase.__call__)
    def __call__(self, state):
        index = state.index
        if index == state.end:
            return True
        
        if self.parser(state):
            state.index = index
            return True
        
        raise EvaluationError(state.array, index, index+1, self.message)
    
    @copy_docs(ParserBase.__repr__)
    def __repr__(self):
        return f'{self.__class__.__name__}({self.parser!r}, {self.message!r})'


class ParserCharRange(ParserBase):
    """
    Parser base for in-range character value checks.
    
    Attributes
    ----------
    start : `int`
        The minimal value what a character's value need to hit.
    end : `int`
        The maximal value what a character's value need to hit.
    """
    __slots__ = ('start', 'end')
    
    def __new__(cls, start, end):
        """
        Creates a new ``ParserCharRange`` instance from the given parameters.
        
        Parameters
        ----------
        start : `str`
            The lowest character, what a character's value should to hit.
        end : `str`
            The highest character, what a character's value should hit.
        """
        start = ord(start)
        end = ord(end)
        
        if start > end:
            start, end = end, start
        
        self = object.__new__(cls)
        self.start = start
        self.end = end
        return self
    
    @copy_docs(ParserBase.__call__)
    def __call__(self, state):
        index = state.index
        if index == state.end:
            return False
        
        value = state.array[index]
        
        if (value >= self.start) and (value <= self.end):
            state.index = index+1
            return True
        
        return False
    
    @copy_docs(ParserBase.__repr__)
    def __repr__(self):
        return f'{self.__class__.__name__}({chr(self.start)!r}, {chr(self.end)!r})'


class ParserOptional(ParserBase):
    """
    Optional parser wrapper.
    
    Attributes
    ----------
    parser : ``ParserBase``
        The internal parser to try to match.
    """
    __slots__ = ('parser', )
    
    def __new__(cls, parser):
        """
        Creates a new ``ParserOptional`` parser instance with the given parser.
        
        Parameters
        ----------
        parser : ``ParserBase``
            The internal parser to mark optional.
        """
        self = object.__new__(cls)
        self.parser = parser
        return self
    
    @copy_docs(ParserBase.__call__)
    def __call__(self, state):
        index = state.index
        success = self.parser(state)
        if not success:
            state.index = index
        
        return True
    
    @copy_docs(ParserBase.__repr__)
    def __repr__(self):
        return f'{self.__class__.__name__}({self.parser!r})'


class ParserRepeat(ParserBase):
    """
    Repeat parser wrapper.
    
    Attributes
    ----------
    parser : ``ParserBase``
        The parser to repeat.
    """
    __slots__ = ('parser', )
    
    def __new__(cls, parser):
        """
        Creates a new ``ParserRepeat`` instance with the given parameters.
        
        Parameters
        ----------
        parser : ``ParserBase``
            The internal parser to repeat.
        """
        self = object.__new__(cls)
        self.parser = parser
        return self
    
    @copy_docs(ParserBase.__call__)
    def __call__(self, state):
        while True:
            success = self.parser(state)
            if success:
                continue
            break
        
        return True
    
    @copy_docs(ParserBase.__repr__)
    def __repr__(self):
        return f'{self.__class__.__name__}({self.parser!r})'


class ParserCharOne(ParserBase):
    """
    Parser to parse one character.
    
    Attributes
    ----------
    value : `int`
        The character's value to match,
    """
    __slots__ = ('value', )
    
    def __new__(cls, value):
        """
        Creates a new ``ParserCharOne`` instance with the given character.
        
        Parameters
        ----------
        value : `str`
            The character to match.
        """
        value = ord(value)
        
        self = object.__new__(cls)
        self.value = value
        return self
    
    @copy_docs(ParserBase.__call__)
    def __call__(self, state):
        index = state.index
        if index == state.end:
            return False
        
        value = state.array[index]
        if value == self.value:
            state.index = index+1
            return True
        
        return False
    
    @copy_docs(ParserBase.__repr__)
    def __repr__(self):
        return f'{self.__class__.__name__}({chr(self.value)!r})'


class ParserCharSequence(ParserBase):
    """
    Creates a parser, which matches a sequence of characters.
    
    Attributes
    ----------
    sequence : `tuple` of `int`
        Sequence of characters to match.
    """
    __slots__ = ('sequence', )
    
    def __new__(cls, sequence):
        """
        Creates a new ``ParserCharSequence`` parser.
        
        Parameters
        ----------
        sequence : `str`
            The string to match.
        """
        sequence = tuple(ord(value) for value in sequence)
        
        self = object.__new__(cls)
        self.sequence = sequence
        return self
    
    @copy_docs(ParserBase.__call__)
    def __call__(self, state):
        index = state.index
        sequence = self.sequence
        
        if index + len(sequence) > state.end:
            return False
        
        array = state.array
        
        for character in sequence:
            value = array[index]
            if value == character:
                index += 1
                continue
            
            return False
        
        state.index = index
        return True
    
    @copy_docs(ParserBase.__repr__)
    def __repr__(self):
        return f'{self.__class__.__name__}({bytes(self.sequence).decode()!r})'


class ParserCharAny(ParserBase):
    """
    Matches any of the stores values.
    
    Attributes
    ----------
    values : `set` of `int`
        The values to match.
    """
    __slots__ = ('values', )
    
    def __new__(cls, characters):
        """
        Creates a new ``ParserCharAny`` parser from the given characters.
        
        Parameters
        ----------
        characters : `iterable` of `str`
            The characters to match.
        """
        values = frozenset(ord(character) for character in characters)
        
        self = object.__new__(cls)
        self.values = values
        return self
    
    @copy_docs(ParserBase.__call__)
    def __call__(self, state):
        index = state.index
        if index == state.end:
            return False
        
        value = state.array[index]
        
        if value in self.values:
            state.index = index+1
            return True
        
        return False
    
    @copy_docs(ParserBase.__repr__)
    def __repr__(self):
        return f'{self.__class__.__name__}([{", ".join(repr(chr(value)) for value in self.values)}])'


class ParserSequence(ParserBase):
    """
    Matches a sequence of parsers.
    
    Attributes
    ----------
    parsers : `tuple` of ``ParserBase``
        The parsers to match in a sequence.
    """
    __slots__ = ('parsers', )
    
    def __new__(cls, parsers):
        """
        Creates a new ``ParserSequence`` instance from the given parsers.
        
        Parameters
        ----------
        parsers : `iterable` of ``ParserBase``
            The parsers to match in a sequence.
        """
        parsers = tuple(parsers)
        if __debug__:
            for parser in parsers:
                if not isinstance(parser, ParserBase):
                    raise AssertionError(f'`{ParserSequence}.__new__` creates with an iterable of not only '
                        f'{ParserBase.__name__} instance, got: {parser.__class__.__name__}; {parser!r}; {parsers!r}.')
        
        self = object.__new__(cls)
        self.parsers = parsers
        return self
    
    @copy_docs(ParserBase.__call__)
    def __call__(self, state):
        index = state.index
        
        for parser in self.parsers:
            if parser(state):
                continue
            
            state.index = index
            return False
        
        return True
    
    @copy_docs(ParserBase.__repr__)
    def __repr__(self):
        return f'{self.__class__.__name__}([{", ".join(repr(parser) for parser in self.parsers)}])'


class ParserAny(ParserBase):
    """
    Tries to match any sub-parser.
    
    Attributes
    ----------
    parsers : `list` of ``ParserBase``
        The parsers to match any of.
    """
    __slots__ = ('parsers', )
    
    def __new__(cls, parsers):
        """
        Creates a new ``ParserAny`` instance from the given parsers.
        
        Parameters
        ----------
        parsers : `iterable` of ``ParserBase``
            The parsers to match any of.
        """
        parsers = list(parsers)
        
        self = object.__new__(cls)
        self.parsers = parsers
        return self

    @copy_docs(ParserBase.__call__)
    def __call__(self, state):
        index = state.index
        
        for parser in self.parsers:
            if parser(state):
                return True
            
            state.index = index
            continue
        
        return False
    
    @copy_docs(ParserBase.__repr__)
    def __repr__(self):
        return f'{self.__class__.__name__}([{", ".join(repr(parser) for parser in self.parsers)}])'


PARSE_DECIMAL = ParserCharRange('0', '9')
PARSE_HEXADECIMAL = ParserAny([
    PARSE_DECIMAL,
    ParserCharRange('a', 'f'),
    ParserCharRange('A', 'F'),
])
PARSE_OCTAL = ParserCharRange('0', '7')
PARSE_BINARY = ParserCharRange('0', '1')

PARSE_OPTIONAL_UNDERSCORE = ParserOptional(
    ParserCharOne('_'),
)

PARSE_ZERO = ParserCharOne('0')

PARSE_NUMERIC_POSTFIX = ParserPostfixCheck(
    ParserCharAny([
        *SPACE_CHARACTERS,
        *OPERATION_CHARACTERS,
        '.',
    ]),
    'Numeric value must be followed by space or an operation.',
)

PARSE_NUMERIC_DECIMAL_POSTFIX = ParserOptional(
    ParserRepeat(
        ParserCharAny(['k', 'K', 'm', 'M', 'g', 'G', 't', 'T']),
    ),
)

PARSE_NUMERIC_FLOAT = ParserIdentifier(
    ParserAny([
        ParserSequence([
            PARSE_DECIMAL,
            ParserRepeat(
                ParserSequence([
                    PARSE_OPTIONAL_UNDERSCORE,
                    PARSE_DECIMAL,
                ]),
            ),
            ParserCharOne('.'),
            ParserOptional(
                ParserSequence([
                    PARSE_DECIMAL,
                    ParserRepeat(
                        ParserSequence([
                            PARSE_OPTIONAL_UNDERSCORE,
                            PARSE_DECIMAL,
                        ]),
                    ),
                ]),
            ),
            PARSE_NUMERIC_POSTFIX,
        ]),
        ParserSequence([
            ParserCharOne('.'),
            PARSE_DECIMAL,
            ParserRepeat(
                ParserSequence([
                    PARSE_OPTIONAL_UNDERSCORE,
                    PARSE_DECIMAL,
                ]),
            ),
            PARSE_NUMERIC_POSTFIX,
        ]),
    ]),
    STATIC_NUMERIC_FLOAT_ID,
)

PARSE_NUMERIC_DECIMAL = ParserIdentifier(
    ParserSequence([
        PARSE_DECIMAL,
        ParserRepeat(
            ParserSequence([
                PARSE_OPTIONAL_UNDERSCORE,
                PARSE_DECIMAL,
            ]),
        ),
        PARSE_NUMERIC_DECIMAL_POSTFIX,
        PARSE_NUMERIC_POSTFIX,
    ]),
    STATIC_NUMERIC_DECIMAL_ID,
)

PARSE_NUMERIC_HEXADECIMAL = ParserIdentifier(
    ParserSequence([
        PARSE_ZERO,
        ParserCharAny(['x', 'X']),
        PARSE_HEXADECIMAL,
        ParserRepeat(
            ParserSequence([
                PARSE_OPTIONAL_UNDERSCORE,
                PARSE_HEXADECIMAL,
            ]),
        ),
        PARSE_NUMERIC_POSTFIX,
    ]),
    STATIC_NUMERIC_HEXADECIMAL_ID,
)

PARSE_NUMERIC_OCTAL = ParserIdentifier(
    ParserSequence([
        PARSE_ZERO,
        ParserCharAny(['o', 'O']),
        PARSE_OCTAL,
        ParserRepeat(
            ParserSequence([
                PARSE_OPTIONAL_UNDERSCORE,
                PARSE_OCTAL,
            ]),
        ),
        PARSE_NUMERIC_POSTFIX,
    ]),
    STATIC_NUMERIC_OCTAL_ID,
)

PARSE_NUMERIC_BINARY = ParserIdentifier(
    ParserSequence([
        PARSE_ZERO,
        ParserCharAny(['b', 'B']),
        PARSE_BINARY,
        ParserRepeat(
            ParserSequence([
                PARSE_OPTIONAL_UNDERSCORE,
                PARSE_BINARY,
            ]),
        ),
        PARSE_NUMERIC_POSTFIX,
    ]),
    STATIC_NUMERIC_BINARY_ID,
)

PARSE_NUMERIC = ParserAny([
    PARSE_NUMERIC_FLOAT,
    PARSE_NUMERIC_DECIMAL,
    PARSE_NUMERIC_HEXADECIMAL,
    PARSE_NUMERIC_OCTAL,
    PARSE_NUMERIC_BINARY,
])

PARSE_OPERATION_1_CHAR = ParserAny([
    ParserIdentifier(
        ParserCharOne(OPERATION_ADD_STRING),
        OPERATION_ADD_ID,
    ),
    ParserIdentifier(
        ParserCharOne(OPERATION_BINARY_AND_STRING),
        OPERATION_BINARY_AND_ID,
    ),
    ParserIdentifier(
        ParserCharOne(OPERATION_SUBTRACTION_STRING),
        OPERATION_SUBTRACTION_ID,
    ),
    ParserIdentifier(
        ParserCharOne(OPERATION_INVERT_STRING),
        OPERATION_INVERT_ID,
    ),
    ParserIdentifier(
        ParserCharOne(OPERATION_BINARY_OR_STRING),
        OPERATION_BINARY_OR_ID,
    ),
    ParserIdentifier(
        ParserCharOne(OPERATION_BINARY_XOR_STRING),
        OPERATION_BINARY_XOR_ID,
    ),
    ParserIdentifier(
        ParserCharOne(OPERATION_PARENTHESES_START_STRING),
        OPERATION_PARENTHESES_START_ID,
    ),
    ParserIdentifier(
        ParserCharOne(OPERATION_PARENTHESES_END_STRING),
        OPERATION_PARENTHESES_END_ID,
    ),
    ParserIdentifier(
        ParserCharOne(OPERATION_REMAINDERS_STRING),
        OPERATION_REMAINDER_ID,
    ),
    ParserIdentifier(
        ParserCharOne(OPERATION_TRUE_DIVISION_STRING),
        OPERATION_TRUE_DIVISION_ID,
    ),
    ParserIdentifier(
        ParserCharOne(OPERATION_MULTIPLY_STRING),
        OPERATION_MULTIPLY_ID,
    ),
])

PARSE_OPERATION_2_CHAR = ParserAny([
    ParserIdentifier(
        ParserCharSequence(OPERATION_LEFT_SHIFT_STRING),
        OPERATION_LEFT_SHIFT_ID,
    ),
    ParserIdentifier(
        ParserCharSequence(OPERATION_RIGHT_SHIFT_STRING),
        OPERATION_RIGHT_SHIFT_ID,
    ),
    ParserIdentifier(
        ParserCharSequence(OPERATION_FULL_DIVISION_STRING),
        OPERATION_FULL_DIVISION_ID,
    ),
    ParserIdentifier(
        ParserCharSequence(OPERATION_POWER_STRING),
        OPERATION_POWER_ID,
    ),
])

PARSE_OPERATION = ParserAny([
    PARSE_OPERATION_2_CHAR,
    PARSE_OPERATION_1_CHAR,
])


PARSE_IDENTIFIER = ParserIdentifier(
    ParserSequence([
        ParserAny([
            ParserCharRange('a', 'z'),
            ParserCharRange('A', 'Z'),
            ParserCharOne('_'),
        ]),
        ParserRepeat(
            ParserAny([
                ParserCharRange('a', 'z'),
                ParserCharRange('A', 'Z'),
                ParserCharOne('_'),
                PARSE_DECIMAL,
            ])
        ),
    ]),
    VARIABLE_IDENTIFIER,
)

PARSE_SPACE_ANY = ParserCharAny([' ', '\t'])

PARSE_SPACE = ParserIdentifier(
    ParserSequence([
        PARSE_SPACE_ANY,
        ParserRepeat(
            PARSE_SPACE_ANY,
        ),
    ]),
    STATIC_NONE_ID,
)

JUST_PARSE = ParserAny([
    PARSE_SPACE,
    PARSE_NUMERIC,
    PARSE_OPERATION,
    PARSE_IDENTIFIER,
])


class EvaluationError(SlashCommandError):
    """
    Exception raised in any parsing related issue.
    
    Attributes
    ----------
    _repr : `None` or `str`
        The generated error message.
    array : `tuple` of `int`
        Source parsed array.
    end : `int`
        The end of the errored part.
    start : `int`
        The start of the errored part.
    message : `str`
        Additional message to forward.
    """
    def __init__(self, array, start, end, message):
        """
        Creates a new ``EvaluationError`` instance from the given parameters.
        
        Parameters
        ----------
        array : `tuple` of `int`
            Source parsed array.
        start : `int`
            The start of the errored part.
        end : `int`
            The end of the errored part.
        message : `str`
            Additional message to forward.
        """
        self.array = array
        self.start = start
        self.end = end
        self.message = message
        self._repr = None
        Exception.__init__(self, array, start, end, message)
    
    def __repr__(self):
        """Returns the representation of the syntax error."""
        repr_ = self._repr
        if repr_ is None:
            repr_ = self._create_repr()
        
        return repr_
    
    def _create_repr(self):
        """
        Creates the representation of the parsing syntax error.
        
        Returns
        -------
        repr_ : `str`
            The representation of the syntax error.
        """
        repr_parts = [self.__class__.__name__, '\n']
        for character in self.array:
            repr_parts.append(chr(character))
        
        repr_parts.append('\n')
        start = self.start
        repr_parts.append(' '*self.start)
        repr_parts.append('^'*(self.end-start))
        repr_parts.append('\n')
        repr_parts.append(self.message)
        repr_ = ''.join(repr_parts)
        self._repr = repr_
        return repr_


class Token:
    """
    Represents a parsed token.
    
    Attributes
    ----------
    array : `list` of `int`
        The parent array.
    end : `int`
        The token's end+1 index in the array.
    id : `int`
        The token's end index inside of the array.
    start : `int`
        The token's start index inside of the array.
    value : `None` or `Any`
        The evaluated value.
    sub_tokens : `None` or `list` of ``Token``
        Sub tokens of the tokens if applicable.
    """
    __slots__ = ('array', 'end', 'id', 'start', 'value', 'sub_tokens')
    
    def __new__(cls, array, start, end, identifier, sub_tokens, value):
        """
        Creates a new ``Token`` instance with the given parameters
        
        Parameters
        ----------
        array : `list` of `int`
            The parent array.
        start : `int`
            The token's start index inside of the array.
        end : `int`
            The token's end+1 index in the array.
        identifier : `int`
            The token's end index inside of the array.
        sub_tokens : `None` or `list` of ``Token``
            Sub tokens of the tokens if applicable.
        value : `None` or `Any`
            The evaluated value.
        """
        self = object.__new__(cls)
        self.array = array
        self.start = start
        self.end = end
        self.id = identifier
        self.value = value
        self.sub_tokens = sub_tokens
        
        return self
    
    def __repr__(self):
        """Returns the token's representation."""
        repr_parts = ['<', self.__class__.__name__, ' ']
        
        repr_parts.append('start=')
        repr_parts.append(repr(self.start))
        
        repr_parts.append(', ')
        repr_parts.append('end=')
        repr_parts.append(repr(self.end))
        
        repr_parts.append(', ')
        repr_parts.append('id=')
        repr_parts.append(repr(self.id))
        
        value = self.value
        if (value is not None):
            repr_parts.append(', ')
            repr_parts.append('value=')
            repr_parts.append(repr(value))
        
        sub_tokens = self.sub_tokens
        if (sub_tokens is not None):
            repr_parts.append(', ')
            repr_parts.append('sub_tokens=')
            repr_parts.append(repr(sub_tokens))
        
        repr_parts.append('>')
        
        return ''.join(repr_parts)


class ParsingState:
    """
    Parsing state storing information between parsers.
    
    Attributes
    ----------
    array : `tuple` of `int`
        The character's numeric values everywhere.
    index : `int`
        The index where the parsing is at.
    end : `int`
        The length of array.
    tokens : `list` of ``Token``
        The parsed tokens.
    """
    __slots__ = ('array', 'index', 'tokens', 'end')
    
    def __new__(cls, text):
        """
        Creates a new ``ParsingState`` from the given text.
        
        Parameters
        ----------
        text : `str`
            A text to evaluate.
        """
        array = tuple(ord(character) for character in text)
        
        self = object.__new__(cls)
        self.array = array
        self.index = 0
        self.end = len(array)
        self.tokens = []
        return self
    
    
    def add_token(self, start, identifier):
        """
        Adds a token to the parsing state.
        
        Parameters
        ----------
        start : `int`
            The position where the token starts.
        identifier : `int`
            The token's identifier.
        
        Raises
        ------
        EvaluationError
            Conversion failed.
        """
        array = self.array
        end = self.index
        evaluator = EVALUATORS.get(identifier, None)
        if evaluator is None:
            value = None
        else:
            value, identifier = evaluator(array[start:end])
            if identifier == STATIC_NONE_ID:
                raise EvaluationError(self.array, start, end, 'Unknown identifier.')
        
        token = Token(self.array, start, end, identifier, None, value)
        self.tokens.append(token)


def parse_cycle(state):
    """
    Runs parsing trough a ``ParsingState`` instance.
    
    Parameters
    ----------
    state : ``ParsingState``
        Respective parsing state.
    
    Raises
    ------
    EvaluationError
        Any syntax error occurred.
    """
    while True:
        if state.end == state.index:
            break
        
        if not JUST_PARSE(state):
            raise EvaluationError(state.array, state.index, state.index+1, 'Unexpected character.')


def optimize_tokens_remove_space(state):
    """
    Removes the spaces from the given tokens.
    
    Parameters
    ----------
    state : ``ParsingState``
        Respective parsing state.
    
    Raises
    ------
    EvaluationError
        Any syntax error occurred.
    """
    tokens = state.tokens
    # Remove spaces
    for index in reversed(range(len(tokens))):
        token = tokens[index]
        if token.id == STATIC_NONE_ID:
            del tokens[index]
    

def check_parentheses(state):
    """
    Checks valid parentheses.
    
    Parameters
    ----------
    state : ``ParsingState``
        Respective parsing state.
    
    Raises
    ------
    EvaluationError
        Any syntax error occurred.
    """
    tokens = state.tokens
    
    parentheses_starts = []
    for token in tokens:
        token_id = token.id
        if token_id == OPERATION_PARENTHESES_START_ID:
            parentheses_starts.append(token)
            continue
        
        if token_id == OPERATION_PARENTHESES_END_ID:
            if parentheses_starts:
                del parentheses_starts[-1]
                continue
            
            raise EvaluationError(token.array, token.start, token.end, 'Never opened parentheses.')
    
    if parentheses_starts:
        token = parentheses_starts[-1]
        raise EvaluationError(token.array, token.start, state.end, 'Never closed parentheses.')

    

def build_parentheses(state):
    """
    Builds parentheses.
    
    Parameters
    ----------
    state : ``ParsingState``
        Respective parsing state.
    """
    tokens = state.tokens
    parentheses_end_indexes = []
    for index in reversed(range(len(tokens))):
        token = tokens[index]
        token_id = token.id
        if token_id == OPERATION_PARENTHESES_END_ID:
            parentheses_end_indexes.append(index)
            continue
        
        if token_id == OPERATION_PARENTHESES_START_ID:
            parentheses_end_index = parentheses_end_indexes.pop()
            
            # Check whether we call a function.
            if parentheses_end_index == 0:
                is_function_call = False
                value = None
                start = token.start
            else:
                maybe_function_token = tokens[index-1]
                if maybe_function_token.id == VARIABLE_FUNCTION:
                    is_function_call = True
                    value = tokens[index-1].value
                    start = maybe_function_token.start
                else:
                    is_function_call = False
                    value = None
                    start = token.start
            
            
            parentheses_difference = parentheses_end_index-index
            if (not is_function_call) and (parentheses_difference == 2):
                token = tokens[index+1]
            else:
                sub_tokens = tokens[index+1:parentheses_end_index]
                parentheses_end_token = tokens[parentheses_end_index]
                
                if is_function_call:
                    identifier = TOKEN_GROUP_FUNCTION_CALL
                else:
                    identifier = TOKEN_GROUP_PARENTHESES
                
                token = Token(state.array, start, parentheses_end_token.end, identifier, sub_tokens, value)
            
            index -= is_function_call
            
            tokens[index] = token
            del tokens[index+1:parentheses_end_index+1]
            parentheses_difference = parentheses_end_index-index
            for parentheses_index in range(len(parentheses_end_indexes)):
                parentheses_end_indexes[parentheses_index] -= parentheses_difference
            
            continue
        
        # no more cases
        continue


def check_followance(state):
    """
    Checks whether token order is bad and such.
    
    Parameters
    ----------
    state : ``ParsingState``
        Respective parsing state.
    
    Raises
    ------
    EvaluationError
        Any syntax error occurred.
    """
    tokens = state.tokens
    if not tokens:
        return
    
    token = tokens[0]
    token_id = token.id
    if token_id in CANT_START:
        raise EvaluationError(token.array, token.start, token.end,
            f'Expression cannot start with {TOKEN_NAMES[token_id]}.'
        )
    
    token = tokens[-1]
    token_id = token.id
    if token_id in CANT_END:
        raise EvaluationError(token.array, token.start, token.end,
            f'Expression cannot end with {TOKEN_NAMES[token_id]}.'
        )
    
    
    last_token_id = tokens[0].id
    
    for index in range(1, len(tokens)):
        try:
            unrepeatable_ids = CANT_FOLLOW[last_token_id]
        except KeyError:
            continue
        
        token = tokens[index]
        token_id = token.id
        if token_id in unrepeatable_ids:
            last_token = tokens[index-1]
            raise EvaluationError(token.array, last_token.start, token.end,
                f'{TOKEN_NAMES[last_token_id]} cannot be followed by {TOKEN_NAMES[token_id]}.'
            )
        
        last_token_id = token_id
        continue


def evaluate_prefix_operations(tokens):
    """
    Evaluates prefix operations.
    
    Parameters
    ----------
    tokens : `list` of ``Token``
        Tokens to evaluate.
    """
    for index in reversed(range(1, len(tokens))):
        token = tokens[index]
        token_id = token.id
        if token_id not in CAN_EXECUTE_PREFIX_PATTERN_3:
            continue
        
        operation_token = tokens[index-1]
        if operation_token.id not in CAN_EXECUTE_PREFIX_PATTERN_2:
            continue
        
        if (index != 1):
            if tokens[index-2].id not in CAN_EXECUTE_PREFIX_PATTERN_1:
                continue
        
        token = EVALUATE_1_SIDED_OPERATION[operation_token.id](operation_token, token)
        del tokens[index]
        tokens[index-1] = token
        
        continue


def evaluate_two_sided_operations(tokens):
    """
    Evaluates two sided operations from the given tokens.
    
    Parameters
    ----------
    tokens : `list` of ``Token``
        Tokens to evaluate.
    
    Returns
    -------
    token : ``Token``
        The final evaluated token.
    """
    limit = len(tokens)-1
    for evaluable_tokens in CAN_EXECUTE_TWO_SIDED_ORDERED:
        index = 1
        while index < limit:
            token = tokens[index]
            token_id = token.id
            if token_id not in evaluable_tokens:
                index += 2
                continue
            
            token = EVALUATE_2_SIDED_OPERATION[token_id](tokens[index-1], token, tokens[index+1])
            tokens[index-1] = token
            del tokens[index:index+2]
            limit -= 2
            continue
        
        if limit == 0:
            break
    
    return tokens[0]


def evaluate_function_call(token):
    """
    Evaluates the given function call's token.
    
    Parameters
    ----------
    token : ``Token``
        The function call token to evaluate.
    
    Returns
    -------
    token : ``Token``
        The evaluated token.
    
    Raises
    ------
    EvaluationError
        Evaluation failed.
    """
    sub_tokens = token.sub_tokens
    if len(sub_tokens) > 1:
        sub_token = evaluate_tokens(sub_tokens)
    else:
        sub_token = sub_tokens[0]
    
    function, validity_checker = token.value
    value = sub_token.value
    
    if (validity_checker is not None):
        validity_checker(token, value)
    
    try:
        value = function(value)
    except BaseException as err:
        raise EvaluationError(token.array, token.start, token.end,
            f'{function.__name__}({value!r}) raised: {err!r}',
        ) from None
    
    return Token(token.array, token.start, token.end, VARIABLE_EVALUATED, None, value)


def evaluate_tokens(tokens):
    """
    Evaluates tokens.
    
    Parameters
    ----------
    tokens : `list` of ``Token``
        Tokens to evaluate.
    
    Returns
    -------
    token : ``Token``
        The final evaluated token.
    """
    for index in range(len(tokens)):
        token = tokens[index]
        token_id = token.id
        if token_id == TOKEN_GROUP_PARENTHESES:
            tokens[index] = evaluate_tokens(token.sub_tokens)
            continue
        
        if token_id == TOKEN_GROUP_FUNCTION_CALL:
            tokens[index] = evaluate_function_call(token)
            continue
    
    evaluate_prefix_operations(tokens)
    evaluate_two_sided_operations(tokens)
    return tokens[0]


def evaluate_text(text):
    """
    Evaluates the given text.
    
    Returns
    -------
    text : `str`
        The text to evaluate.
    
    Returns
    -------
    value : `int` or `float`
        The evaluation's result.
    
    Raises
    ------
    EvaluationError
        Any exception occurred meanwhile evaluating the given text.
    """
    state = ParsingState(text)
    parse_cycle(state)
    optimize_tokens_remove_space(state)
    check_followance(state)
    check_parentheses(state)
    build_parentheses(state)
    token = evaluate_tokens(state.tokens)
    return token.value
