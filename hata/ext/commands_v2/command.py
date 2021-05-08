# -*- coding: utf-8 -*-
__all__ = ('Command', )
import re, reprlib

from ...backend.utils import WeakReferer

from ...discord.events.handling_helpers import route_value, check_name, Router, route_name, _EventHandlerManager
from ...discord.interaction import InteractionEvent
from ...discord.preconverters import preconvert_bool

from .utils import CommandWrapper
from .category import Category
from .command_helpers import test_error_handler, raw_name_to_display, normalize_description, validate_checks, \
    validate_error_handlers

def _check_maybe_route(variable_name, variable_value, route_to, validator):
    """
    Helper class of ``Command`` parameter routing.
    
    Parameters
    ----------
    variable_name : `str`
        The name of the respective variable
    variable_value : `str`
        The respective value to route maybe.
    route_to : `int`
        The value how much times the routing should happen. by default should be given as `0` if no routing was
        done yet.
    validator : `callable` or `None`
        A callable, what validates the given `variable_value`'s value and converts it as well if applicable.
    
    Returns
    -------
    processed_value : `str`
        Processed value returned by the `validator`. If routing is happening, then a `tuple` of those values is
        returned.
    route_to : `int`
        The amount of values to route to.
    
    Raises
    ------
    ValueError
        Value is routed but to a bad count amount.
    BaseException
        Any exception raised by `validator`.
    """
    if (variable_value is not None) and isinstance(variable_value, tuple):
        route_count = len(variable_value)
        if route_count == 0:
            processed_value = None
        elif route_count == 1:
            variable_value = variable_value[0]
            if variable_value is ...:
                variable_value = None
            
            if validator is None:
                processed_value = variable_value
            else:
                processed_value = validator(variable_value)
        else:
            if route_to == 0:
                route_to = route_count
            elif route_to == route_count:
                pass
            else:
                raise ValueError(f'`{variable_name}` is routed to `{route_count}`, meanwhile something else is '
                    f'already routed to `{route_to}`.')
            
            if validator is None:
                processed_value = variable_value
            else:
                processed_values = []
                for value in variable_value:
                    if (value is not ...):
                        value = validator(value)
                    
                    processed_values.append(value)
                
                processed_value = tuple(processed_values)
    
    else:
        if validator is None:
            processed_value = variable_value
        else:
            processed_value = validator(variable_value)
    
    return processed_value, route_to


def _validate_hidden(hidden):
    """
    Validates the given `is_global` value.
    
    Parameters
    ----------
    hidden : `None` or `bool`
        The `hidden` value to validate.
    
    Returns
    -------
    hidden : `bool`
        The validated `hidden` value.
    
    Raises
    ------
    TypeError
        If `hidden` was not given as `None` nor as `bool` instance.
    """
    if hidden is None:
        hidden = False
    else:
        hidden = preconvert_bool(hidden, 'hidden')
    
    return hidden


def _validate_hidden_if_checks_fail(hidden_if_checks_fail):
    """
    Validates the given `hidden_if_checks_fail` value.
    
    Parameters
    ----------
    hidden_if_checks_fail : `None` or `bool`
        The `hidden_if_checks_fail` value to validate.
    
    Returns
    -------
    hidden_if_checks_fail : `bool`
        The validated `hidden` value.
    
    Raises
    ------
    TypeError
        If `hidden_if_checks_fail` was not given as `None` nor as `bool` instance.
    """
    if hidden_if_checks_fail is None:
        hidden_if_checks_fail = True
    else:
        hidden_if_checks_fail = preconvert_bool(hidden_if_checks_fail, 'hidden_if_checks_fail')
    
    return hidden_if_checks_fail


def _validate_name(name):
    """
    Validates the given name.
    
    Parameters
    ----------
    name : `None` or `str`
        A command's respective name.
    
    Returns
    -------
    name : `None` or `str`
        The validated name.
    
    Raises
    ------
    TypeError
        If `name` is not given as `str` instance.
    """
    if name is not None:
        name_type = name.__class__
        if name_type is str:
            pass
        elif issubclass(name_type, str):
            name = str(name)
        else:
            raise TypeError(f'`name` can be only given as `None` or as `str` instance, got {name_type.__name__}; '
                f'{name!r}.')
    
    return name


def _validate_aliases(aliases):
    """
    Validates the given aliases.
    
    Parameters
    ----------
    aliases : `None`, `str` or `list` of `str`
        Command aliases.
    
    Returns
    -------
    aliases : `None` or `set` of `str`
        The validated aliases.
    
    Raises
    ------
    TypeError
        `aliases` was not given as `None`, `str`, neither as `list` of `str` instances.
    ValueError
        `aliases` contains an empty string.
    """
    if (aliases is not None):
        if isinstance(aliases, list):
            for alias in aliases:
                if not isinstance(alias, str):
                    raise TypeError(f'A non `str` instance alias is given: {alias!r}, got {aliases!r}.')
                
                if not alias:
                    raise ValueError(f'An alias cannot be empty string, got {aliases!r}.')
            
            aliases_processed = set()
            for alias in aliases:
                alias = raw_name_to_display(alias)
                aliases_processed.add(alias)
            
            if aliases_processed:
                aliases = aliases_processed
            else:
                aliases = None
        
        elif isinstance(aliases, str):
            if not aliases:
                raise ValueError(f'An alias cannot be empty string, got {aliases!r}.')
            
            aliases = raw_name_to_display(aliases)
            aliases = {aliases}
        else:
            raise TypeError('Aliases can be given as `str`, or `list` of `str` instances, got '
                f'{aliases.__class__.__name__}; {aliases!r}')
    
    return aliases


def _validate_category(category):
    """
    Validates the given category.
    
    Parameters
    ----------
    category : `None`, `str`  instance or ``Category``
        The category to validate.
    
    Returns
    -------
    category : `str` or ``Category``
        The validated category.
    
    Raises
    ------
    TypeError
        Category is not given either as `None`, `str` instance, or ``Category``.
    """
    if (category is not None):
        category_type = category.__class__
        if category_type is Category:
            pass
        elif category_type is str:
            pass
        elif issubclass(category_type, str):
            category = str(category)
        else:
            raise TypeError(f'`category` should be `None`, type `str` or `{Category.__name__}`, got '
                f'{category_type.__name__}.')
    
    return category


def _generate_description_from(command, description):
    """
    Generates description from the command and it's maybe given description.
    
    Parameters
    ----------
    command : `str`
        The command's function.
    description : `Any`
        The command's description.
    
    Returns
    -------
    description : `str`
        The generated description.
    """
    if description is None:
        description = getattr(command, '__doc__', None)
    
    if (description is not None) and isinstance(description, str):
        description = normalize_description(description)
    
    return description


def _generate_category_hint_from(category):
    """
    Generates category hint from the given category.
    
    Parameters
    ----------
    category : `None`, `str` or ``Category``
        The respective category.
    
    Returns
    -------
    category_hint : `None` or `str`
        The category's string representation if applicable.
    
    Raises
    ------
    TypError
        Category is not given as `None`, `str`, neither as ``Category`` instance.
    """
    if category is None:
        category_hint = None
    else:
        category_type = category.__class__
        if category_type is Category:
            category_hint = category.name
        elif category_type is str:
            category_hint = category
        elif issubclass(category_type, str):
            category_hint = str(category)
        else:
            raise TypeError(f'`category` should be `None`, type `str` or `{Category.__name__}`, got '
                f'{category_type.__name__}.')
    
    return category_hint


class Command:
    """
    Represents a command.
    
    Attributes
    ----------
    _category_hint : `str` or `None`
        Hint for the command processor to detect under which category the command should go.
    _category_reference : `None` or ``WeakReferer`` to ``Category``.
        Weak reference to the command's category.
    _checks : `None` or `tuple` of ``CheckBase``
        The checks of the commands.
    _command : `None` or ``CommandFunction``
        The actual command of the command to maybe call.
    _command_processor_reference : `None` or ``WeakReferer`` to ``CommandProcessor``.
        Weak reference to the command's command processor.
    _error_handlers : `None` or `list` of `function`
        Error handlers bind to the command.
    _sub_commands : `None` or `dict` of (`str`, ``CommandCategory``) items
        Sub command categories of the command.
    aliases : `None` or `list` of `str`
        Name aliases of the command if any. They are always lower case.
    description : `Any`
        The command's description if any.
    display_name : `str`
        The command's display name.
    hidden : `bool`
        Whether the command should be hidden from help commands.
    hidden_if_checks_fail : bool`
        Whether the command should be hidden from help commands if the user's checks fail.
    name : `str`
        The command's name. Always lower case.
    """
    __slots__ = ('_category_hint', '_category_reference', '_checks', '_command', '_command_processor_reference',
        '_error_handlers', '_sub_commands', 'aliases', 'description', 'display_name', 'hidden',
        'hidden_if_checks_fail', 'name')
    
    
    def _iter_checks(self):
        """
        Iterates over all the checks applied to the command.
        
        This method is a generator, which should be used inside of a for loop.
        
        Yields
        ------
        check : ``CheckBase``
        """
        checks = self._checks
        if (checks is not None):
            yield from checks
        
        category_reference = self._category_reference
        if (category_reference is not None):
            category = category_reference()
            if (category is not None):
                checks = category._checks
                if (checks is not None):
                    yield from checks
    
    
    def _iter_error_handlers(self):
        """
        Iterates over all the error handlers applied to the command.
        
        This method is a generator, which should be used inside of a for loop.
        
        Yields
        ------
        error_handler : `function`
        """
        error_handlers = self._error_handlers
        if (error_handlers is not None):
            yield from error_handlers
        
        category_reference = self._category_reference
        if (category_reference is not None):
            category = category_reference()
            if (category is not None):
                error_handlers = category._error_handlers
                if (error_handlers is not None):
                    yield from error_handlers
        
        command_processor_reference = self._command_processor_reference
        if (command_processor_reference is not None):
            command_processor = command_processor_reference()
            if (command_processor is not None):
                error_handlers = command_processor._error_handlers
                if (error_handlers is not None):
                    yield from error_handlers
    
    
    def _iter_names(self):
        """
        Iterates overt he command's names.

        This method is a generator, which should be used inside of a for loop.
        
        Yields
        ------
        command_name : `str`
        """
        yield self.name
        aliases = self.aliases
        if (aliases is not None):
            yield from aliases
    
    
    def get_category(self):
        """
        Returns the command's category if has any.
        
        Returns
        -------
        category : `None` or ``Category``
        """
        category_reference = self._category_reference
        if category_reference is None:
            category = None
        else:
            category = category_reference()
        
        return category
    
    
    def unlink_category(self):
        """
        Unlinks the command from it's category and of it's command processor as well.
        """
        command_processor = self.get_command_processor()
        self._command_processor_reference = None
        if (command_processor is not None):
            command_name_to_command = command_processor.command_name_to_command
            for name in self._iter_names():
                try:
                    command = command_name_to_command[name]
                except KeyError:
                    pass
                else:
                    if command is self:
                        del command_name_to_command[name]
            
            command_processor.registered_commands.discard(self)
        
        
        category = self.get_category()
        self._category_reference = None
        if (category is not None):
            category.registered_commands.discard(self)
    
    
    def set_category(self, category):
        """
        Sets the command's category.
        
        Parameters
        ----------
        category : ``Category``
            The new category of the command.
        
        Raises
        ------
        RuntimeError
            - The command is bound to a category of an other command processor.
            - The command would only partially overwrite
        """
        self.unlink_category()
        
        category.registered_commands.add(self)
        self._category_hint = category.name
        self._category_reference = category._self_reference
        
        command_processor = category.get_command_processor()
        if (command_processor is not None):
            self.set_command_processor(command_processor)
    
    
    def set_command_processor(self, command_processor):
        """
        Sets the command's command processor.
        
        Parameters
        ----------
        command_processor : ``CommandProcessor``
            The command processor to set.
        
        Raises
        ------
        RuntimeError
            - The command is bound to a category of an other command processor.
            - The command would only partially overwrite
        """
        names = set(self._iter_names())
        command_name_to_command = command_processor.command_name_to_command
        
        would_overwrite_commands = set()
        for name in names:
            added_command = command_name_to_command.get(name, None)
            if added_command is None:
                continue
            
            would_overwrite_commands.add(added_command)
        
        for would_overwrite_command in would_overwrite_commands:
            if not names.issubset(would_overwrite_command._iter_names()):
                raise RuntimeError(f'{Command.__name__}: {self!r} would partially overwrite an other command: '
                    f'{would_overwrite_command!r}.')
        
        for name in names:
            command_name_to_command[name] = self
    
    
    def get_command_processor(self):
        """
        Returns the command's command processor if has any.
        
        Returns
        -------
        command_processor : `None` or ``CommandProcessor``
        """
        command_processor_reference = self._command_processor_reference
        if command_processor_reference is None:
            command_processor = None
        else:
            command_processor = command_processor_reference()
        
        return command_processor
    
    
    def error(self, error_handler):
        """
        Adds na error handler to the command.
        
        Parameters
        ----------
        error_handler : `async-callable`
            The error handler to add.
            
            The following parameters are passed to each error handler:
            
            +-------------------+-----------------------+
            | Name              | Type                  |
            +===================+=======================+
            | command_context   | ``CommandContext``    |
            +-------------------+-----------------------+
            | exception         | `BaseException`       |
            +-------------------+-----------------------+
            
            Should return the following parameters:
            
            +-------------------+-----------+
            | Name              | Type      |
            +===================+===========+
            | handled           | `bool`    |
            +-------------------+-----------+
        
        Returns
        -------
        error_handler : `async-callable`
        
        Raises
        ------
        TypeError
            - If `error_handler` accepts bad amount of arguments.
            - If `error_handler` is not async.
        """
        test_error_handler(error_handler)
        
        error_handlers = self._error_handlers
        if error_handlers is None:
            error_handlers = self._error_handlers = []
            
            error_handlers.append(error_handler)
        
        return error_handler
    
    
    @classmethod
    def from_class(cls, klass, kwargs=None):
        """
        The method used, when creating a ``Command`` object from a class.
        
        Extra `kwargs` are supported as well for special the use cases.
        
        Parameters
        ----------
        klass : `type`
            The class, from what's attributes the command will be created.
        
        Returns
        -------
        self : ``Command`` or ``Router``
        
        Raises
        ------
        TypeError
            If any attribute's or value's type is incorrect.
        ValueError
            If any attribute's or value's type is correct, but it's type isn't.
        """
        if not isinstance(klass, type):
            raise TypeError(f'Expected `type` instance, got {klass.__class__.__name__}.')
        
        name = getattr(klass, 'name', None)
        if name is None:
            name = klass.__name__
        
        command = getattr(klass, 'command', None)
        if command is None:
            while True:
                command = getattr(klass, name, None)
                if (command is not None):
                    break
                
                raise ValueError('`command` class attribute is missing.')
        
        description = getattr(klass, 'description', None)
        if description is None:
            description = klass.__doc__
        
        aliases = getattr(klass, 'aliases', None)
        
        category = getattr(klass, 'category', None)
        
        checks_ = getattr(klass, 'checks', None)
        if checks_ is None:
            checks_ = getattr(klass, 'checks_', None)
        
        separator = getattr(klass, 'separator', None)
        
        assigner = getattr(klass, 'assigner', None)
        
        error_handlers = getattr(klass, 'error', None)
        
        hidden = getattr(klass, 'hidden', None)
        
        hidden_if_checks_fail = getattr(klass, 'hidden_if_checks_fail', None)
        
        if (kwargs is not None) and kwargs:
            if (description is None):
                description = kwargs.pop('description', None)
            else:
                try:
                    del kwargs['description']
                except KeyError:
                    pass
            
            if (category is None):
                category = kwargs.pop('category', None)
            else:
                try:
                    del kwargs['category']
                except KeyError:
                    pass
            
            if (checks_ is None) or not checks_:
                checks_ = kwargs.pop('checks', None)
            else:
                try:
                    del kwargs['checks']
                except KeyError:
                    pass
            
            if (separator is None):
                separator = kwargs.pop('separator', None)
            else:
                try:
                    del kwargs['separator']
                except KeyError:
                    pass
            
            if (assigner is None):
                assigner = kwargs.pop('assigner', None)
            else:
                try:
                    del kwargs['assigner']
                except KeyError:
                    pass
            
            if (aliases is None):
                aliases = kwargs.pop('aliases', None)
            else:
                try:
                    del kwargs['aliases']
                except KeyError:
                    pass
            
            if (error_handlers is None):
                error_handlers = kwargs.pop('error', None)
            else:
                try:
                    del kwargs['error']
                except KeyError:
                    pass
            
            if (hidden is None):
                hidden = kwargs.pop('hidden', None)
            else:
                try:
                    del kwargs['hidden']
                except KeyError:
                    pass
            
            if (hidden_if_checks_fail is None):
                hidden_if_checks_fail = kwargs.pop('hidden_if_checks_fail', None)
            else:
                try:
                    del kwargs['hidden_if_checks_fail']
                except KeyError:
                    pass
            
            if kwargs:
                raise TypeError(f'`{cls.__name__}.from_class` did not use up some kwargs: `{kwargs!r}`.')
        
        return cls(command, name, description, aliases, category, checks_, error_handlers, separator, assigner,
            hidden, hidden_if_checks_fail)
    
    @classmethod
    def from_kwargs(cls, command, name, kwargs):
        """
        Called when a command is created before adding it to a ``CommandProcesser``.
        
        Parameters
        ----------
        command : `async-callable`
            The async callable added as the command itself.
        name : `str`, `None`, `tuple` of (`str`, `Ellipsis`, `None`)
            The name to be used instead of the passed `command`'s.
        kwargs : `None` or `dict` of (`str`, `Any`) items.
            Additional keyword arguments.
        
        Returns
        -------
        self : ``Command`` or ``Router``
        
        Raises
        ------
        TypeError
            If any value's type is incorrect.
        ValueError
            If any value's type is correct, but it's type isn't.
        """
        if (kwargs is None) or (not kwargs):
            description = None
            aliases = None
            category = None
            checks_ = None
            error_handlers = None
            separator = None
            assigner = None
            hidden = None
            hidden_if_checks_fail = None
        else:
            description = kwargs.pop('description', None)
            aliases = kwargs.pop('aliases', None)
            category = kwargs.pop('category', None)
            checks_ = kwargs.pop('checks', None)
            error_handlers = kwargs.pop('error', None)
            separator = kwargs.pop('separator', None)
            assigner = kwargs.pop('assigner', None)
            hidden = kwargs.pop('hidden', None)
            hidden_if_checks_fail = kwargs.pop('hidden_if_checks_fail', None)
            
            if kwargs:
                raise TypeError(f'type `{cls.__name__}` not uses: `{kwargs!r}`.')
        
        return cls(command, name, description, aliases, category, checks_, error_handlers, separator, assigner,
            hidden, hidden_if_checks_fail)
    
    
    def __new__(cls, command, name, description, aliases, category, checks_, error_handlers, separator, assigner,
            hidden, hidden_if_checks_fail):
        """
        Creates a new ``Command`` object.
        
        Parameters
        ----------
        command : `None`, `async-callable`
            The async callable added as the command itself.
        name : `None`, `str` or `tuple` of (`None`, `Ellipsis`, `str`)
            The name to be used instead of the passed `command`'s.
        description : `None`, `Any` or `tuple` of (`None`, `Ellipsis`, `Any`)
            Description added to the command. If no description is provided, then it will check the commands's
            `.__doc__` attribute for it. If the description is a string instance, then it will be normalized with the
            ``normalize_description`` function. If it ends up as an empty string, then `None` will be set as the
            description.
        aliases : `None`, `str`, `list` of `str` or `tuple` of (`None, `Ellipsis`, `str`, `list` of `str`)
            The aliases of the command.
        category : `None`, ``Category``, `str` or `tuple` of (`None`, `Ellipsis`, ``Category``, `str`)
            The category of the command. Can be given as the category itself, or as a category's name. If given as
            `None`, then the command will go under the command processer's default category.
        checks_ : `None`, ``CommandCheckWrapper``, ``CheckBase``, `list` of ``CommandCheckWrapper``, ``CheckBase`` \
                instances or `tuple` of (`None`, `Ellipsis`, ``CommandCheckWrapper``, ``CheckBase`` or `list` of \
                ``CommandCheckWrapper``, ``CheckBase``)
            Checks to decide in which circumstances the command should be called.
        error_handlers : `None`, `async-callable`, `list` of `async-callable`, `tuple` of (`None`, `async-callable`, \
                `list` of `async-callable`)
            Error handlers for the command.
        separator : `None`, `str` or `tuple` (`str`, `str`)
            The parameter separator of the command's parser.
        assigner : `None`, `str`
            Parameter assigner sign of the command's parser.
        hidden : `None`, `bool`, `tuple` (`None`, `Ellipsis`, `bool`)
            Whether the command should be hidden from the help commands.
        hidden_if_checks_fail : `None`, `bool`, `tuple` (`None`, `Ellipsis`, `bool`)
            Whether the command should be hidden from the help commands if any check fails.
        """
        if isinstance(command, CommandWrapper):
            function, wrappers = command.fetch_function_and_wrappers_back()
        else:
            function = command
            wrappers = None
        
        route_to = 0
        name, route_to = _check_maybe_route('name', name, route_to, _validate_name)
        description, route_to = _check_maybe_route('description', description, route_to, None)
        aliases, route_to = _check_maybe_route('aliases', aliases, route_to, _validate_aliases)
        category, route_to = _check_maybe_route('category', category, route_to, _validate_category)
        checks_, route_to = _check_maybe_route('checks_', checks_, route_to, validate_checks)
        error_handlers, route_to = _check_maybe_route('error_handlers', error_handlers, route_to,
            validate_error_handlers)
        hidden, route_to = _check_maybe_route('hidden', hidden, route_to, _validate_hidden)
        hidden_if_checks_fail, route_to = _check_maybe_route('hidden_if_checks_fail', hidden_if_checks_fail, route_to,
            _validate_hidden_if_checks_fail)
        
        
        if route_to:
            name = route_name(command, name, route_to)
            default_description = _generate_description_from(command, None)
            description = route_value(description, route_to, default=default_description)
            aliases = route_value(aliases, route_to)
            category = route_value(category, route_to)
            checks_ = route_value(checks_, route_to)
            error_handlers = route_value(error_handlers, route_to)
            hidden = route_value(hidden, route_to)
            hidden_if_checks_fail = route_value(hidden_if_checks_fail, route_to)
            
            category_hint = [_generate_category_hint_from(category) for category in category]

            description = [
                _generate_description_from(command, description)
                    if ((description is None) or (description is not default_description)) else default_description
                for description in description]
        else:
            name = check_name(command, name)
            description = _generate_description_from(command, description)
            category_hint = _generate_category_hint_from(category)
        









