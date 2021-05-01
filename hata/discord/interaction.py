# -*- coding: utf-8 -*-
__all__ = ('ApplicationCommand', 'ApplicationCommandInteraction', 'ApplicationCommandInteractionOption',
    'ApplicationCommandOption', 'ApplicationCommandOptionChoice', 'InteractionResponseTypes',
    'ApplicationCommandPermission', 'ApplicationCommandPermissionOverwrite', 'Component', 'ComponentBase',
    'ComponentInteraction')

import reprlib

from ..backend.utils import modulize, copy_docs
from ..backend.export import export

from .bases import DiscordEntity
from .preinstanced import ApplicationCommandOptionType, InteractionType, ApplicationCommandPermissionOverwriteType, \
    ComponentType, ButtonStyle
from .client_core import APPLICATION_COMMANDS, ROLES
from .preconverters import preconvert_preinstanced_type
from .utils import is_valid_application_command_name, DATETIME_FORMAT_CODE, url_cutter
from .limits import APPLICATION_COMMAND_NAME_LENGTH_MIN, APPLICATION_COMMAND_NAME_LENGTH_MAX, \
    APPLICATION_COMMAND_DESCRIPTION_LENGTH_MIN, APPLICATION_COMMAND_DESCRIPTION_LENGTH_MAX, \
    APPLICATION_COMMAND_CHOICES_MAX, APPLICATION_COMMAND_OPTIONS_MAX, APPLICATION_COMMAND_CHOICE_NAME_LENGTH_MIN, \
    APPLICATION_COMMAND_CHOICE_NAME_LENGTH_MAX, APPLICATION_COMMAND_CHOICE_VALUE_LENGTH_MIN, \
    APPLICATION_COMMAND_CHOICE_VALUE_LENGTH_MAX, APPLICATION_COMMAND_PERMISSION_OVERWRITE_MAX, \
    COMPONENT_SUB_COMPONENT_LIMIT, COMPONENT_LABEL_LENGTH_MAX, COMPONENT_CUSTOM_ID_LENGTH_MAX
from .channel import create_partial_channel
from .user import User, UserBase, ClientUserBase
from .role import Role
from .client_utils import maybe_snowflake
from .emoji import create_partial_emoji, Emoji, create_partial_emoji_data

APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_USER = ApplicationCommandPermissionOverwriteType.user
APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_ROLE = ApplicationCommandPermissionOverwriteType.role

COMPONENT_TYPE_ACTION_ROW = ComponentType.action_row
COMPONENT_TYPE_BUTTON = ComponentType.button

COMPONENT_TYPE_ATTRIBUTE_COMPONENTS = frozenset((COMPONENT_TYPE_ACTION_ROW,))
COMPONENT_TYPE_ATTRIBUTE_CUSTOM_ID = frozenset((COMPONENT_TYPE_BUTTON,))
COMPONENT_TYPE_ATTRIBUTE_ENABLED = frozenset((COMPONENT_TYPE_BUTTON,))
COMPONENT_TYPE_ATTRIBUTE_EMOJI = frozenset((COMPONENT_TYPE_BUTTON,))
COMPONENT_TYPE_ATTRIBUTE_LABEL = frozenset((COMPONENT_TYPE_BUTTON,))
COMPONENT_TYPE_ATTRIBUTE_STYLE = frozenset((COMPONENT_TYPE_BUTTON,))
COMPONENT_TYPE_ATTRIBUTE_URL = frozenset((COMPONENT_TYPE_BUTTON,))


class ApplicationCommand(DiscordEntity, immortal=True):
    """
    Represents a Discord slash command.
    
    Attributes
    ----------
    id : `int`
        The application command's id.
    allow_by_default : `bool`
        Whether the command is enabled by default for everyone who has `use_application_commands` permission.
    application_id : `int`
        The application command's application's id.
    description : `str`
        The command's description. It's length can be in range [2:100].
    name : `str`
        The name of the command. It's length can be in range [1:32].
    options : `None` or `list` of ``ApplicationCommandOption``
        The parameters of the command. It's length can be in range [0:25]. If would be set as empty list, instead is
        set as `None`.
    
    Notes
    -----
    ``ApplicationCommand`` instances are weakreferable.
    """
    __slots__ = ('allow_by_default', 'application_id', 'description', 'name', 'options')
    
    def __new__(cls, name, description, *, allow_by_default=True, options=None):
        """
        Creates a new ``ApplicationCommand`` instance with the given parameters.
        
        Parameters
        ----------
        name : `str`
            The name of the command. It's length can be in range [1:32].
        description : `str`
            The command's description. It's length can be in range [2:100].
        allow_by_default : `bool`, Optional (Keyword only)
            Whether the command is enabled by default for everyone who has `use_application_commands` permission.
            
            Defaults to `True`.
        options : `None` or (`list` or `tuple`) of ``ApplicationCommandOption``, Optional (Keyword only)
            The parameters of the command. It's length can be in range [0:25].
        
        Raises
        ------
        AssertionError
            - If `name` was not given as `str` instance.
            - If `name` length is out of range [1:32].
            - If `name` contains unexpected character.
            - If `description` was not given as `str` instance.
            - If `description` length is out of range [1:100].
            - If `options` was not given neither as `None` nor as (`list` or `tuple`) of ``ApplicationCommandOption``
                instances.
            - If `options`'s length is out of range [0:25].
            - If `allow_by_default` was not given as `bool` instance.
        """
        if __debug__:
            if not isinstance(name, str):
                raise AssertionError(f'`name` can be given as `str` instance, got {name.__class__.__name__}.')
            
            name_length = len(name)
            if name_length < APPLICATION_COMMAND_NAME_LENGTH_MIN or name_length > APPLICATION_COMMAND_NAME_LENGTH_MAX:
                raise AssertionError(f'`name` length can be in range '
                    f'[{APPLICATION_COMMAND_NAME_LENGTH_MIN}:{APPLICATION_COMMAND_NAME_LENGTH_MAX}], got '
                    f'{name_length!r}; {name!r}.')
            
            if not is_valid_application_command_name(name):
                raise AssertionError(f'`name` contains an unexpected character; Got {name!r}.')
            
            if not isinstance(description, str):
                raise AssertionError(f'`description` can be given as `str` instance, got '
                    f'{description.__class__.__name__}.')
            
            description_length = len(description)
            if description_length < APPLICATION_COMMAND_DESCRIPTION_LENGTH_MIN or \
                    description_length > APPLICATION_COMMAND_DESCRIPTION_LENGTH_MAX:
                raise AssertionError(f'`description` length can be in range '
                    f'[{APPLICATION_COMMAND_DESCRIPTION_LENGTH_MIN}:{APPLICATION_COMMAND_DESCRIPTION_LENGTH_MAX}], '
                    f'got {description_length!r}; {description!r}.')
            
            if not isinstance(allow_by_default, bool):
                raise AssertionError(f'`allow_by_default` can be given as `bool` instance, got '
                    f'{allow_by_default.__class__.__name__}.')
        
        if options is None:
            options_processed = None
        else:
            if __debug__:
                if not isinstance(options, (tuple, list)):
                    raise AssertionError(f'`options` can be given as `None` or (`list` or `tuple`) of '
                        f'`{ApplicationCommandOption.__name__}`, got {options.__class__.__name__}.')
            
            # Copy it
            options_processed = list(options)
            if options_processed:
                if __debug__:
                    if len(options_processed) > APPLICATION_COMMAND_OPTIONS_MAX:
                        raise AssertionError(f'`options` length can be in range '
                            f'[0:{APPLICATION_COMMAND_OPTIONS_MAX}], got {len(options_processed)!r}; {options!r}')
                    
                    for index, option in enumerate(options_processed):
                        if not isinstance(option, ApplicationCommandOption):
                            raise AssertionError(f'`options` was given either as `list` or `tuple`, but it\'s element '
                                f'At index {index!r} is not {ApplicationCommandOption.__name__} instance, but '
                                f'{option.__class__.__name__}.')
            
            else:
                options_processed = None
        
        self = object.__new__(cls)
        self.id = 0
        self.application_id = 0
        self.name = name
        self.description = description
        self.allow_by_default = allow_by_default
        self.options = options_processed
        return self
    
    def add_option(self, option):
        """
        Adds a new option to the application command.
        
        Parameters
        ----------
        option : ``ApplicationCommandOption``
            The option to add.
        
        Returns
        -------
        self : ``ApplicationCommand``
        
        Raises
        ------
        AssertionError
            - If the entity is not partial.
            - If `option` is not ``ApplicationCommandOption`` instance.
            - If the ``ApplicationCommand`` has already `25` options.
        """
        if __debug__:
            if self.id != 0:
                raise AssertionError(f'{self.__class__.__name__}.add_option` can be only called on partial '
                    f'`{self.__class__.__name__}`-s, but was called on {self!r}.')
        
        if __debug__:
            if not isinstance(option, ApplicationCommandOption):
                raise AssertionError(f'`option` can be given as {ApplicationCommandOption.__name__} instance, got '
                    f'{option.__class__.__name__}.')
        
        options = self.options
        if options is None:
            self.options = options = []
        else:
            if __debug__:
                if len(options) >= APPLICATION_COMMAND_OPTIONS_MAX:
                    raise AssertionError(f'`option` cannot be added if the {ApplicationCommandOption.__name__} has '
                        f'already `{APPLICATION_COMMAND_OPTIONS_MAX}` options.')
        
        options.append(option)
        return self
    
    @classmethod
    def from_data(cls, data):
        """
        Creates a new ``ApplicationCommand`` from requested data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Received application command data.
        
        Returns
        -------
        self : ``ApplicationCommand``
            The created application command instance.
        """
        application_command_id = int(data['id'])
        try:
            self = APPLICATION_COMMANDS[application_command_id]
        except KeyError:
            self = object.__new__(cls)
            self.id = application_command_id
            self.application_id = int(data['application_id'])
            APPLICATION_COMMANDS[application_command_id] = self
        
            # Discord might not include attributes in edit data, so we will set them first to avoid unset attributes.
            self.description = ''
            self.name = ''
            self.options = None
            self.allow_by_default = True
        
        self._update_no_return(data)
        return self
    
    def _update_no_return(self, data):
        """
        Updates the application command with the given data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Received application command data.
        """
        try:
            self.description = data['description']
        except KeyError:
            pass
        
        try:
            self.name = data['name']
        except KeyError:
            pass
        
        try:
            option_datas = data['options']
        except KeyError:
            pass
        else:
            if (option_datas is None) or (not option_datas):
                options = None
            else:
                options = [ApplicationCommandOption.from_data(option_data) for option_data in option_datas]
            self.options = options
        
        try:
            self.allow_by_default = data['default_permission']
        except KeyError:
            pass
        
    def _update(self, data):
        """
        Updates the application command with the given data and returns the updated attributes in a dictionary with the
        attribute names as the keys and their old value as the values.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Received application command data.
        
        Returns
        -------
        old_attributes : `dict` of (`str`, `Any`) items
            The updated attributes.
            
            Every item in the returned dict is optional and can contain the following ones:
            
            +-----------------------+---------------------------------------------------+
            | Keys                  | Values                                            |
            +=======================+===================================================+
            | description           | `str`                                             |
            +-----------------------+---------------------------------------------------+
            | allow_by_default      | `bool`                                            |
            +-----------------------+---------------------------------------------------+
            | name                  | `str`                                             |
            +-----------------------+---------------------------------------------------+
            | options               | `None` or `list` of ``ApplicationCommandOption``  |
            +-----------------------+---------------------------------------------------+
        """
        old_attributes = {}
        
        try:
            description = data['description']
        except KeyError:
            pass
        else:
            if self.description != description:
                old_attributes['description'] = self.description
                self.description = description
        
        try:
            name = data['name']
        except KeyError:
            pass
        else:
            if self.name != name:
                old_attributes['name'] = self.name
                self.name = name
        
        try:
            option_datas = data['options']
        except KeyError:
            pass
        else:
            if (option_datas is None) or (not option_datas):
                options = None
            else:
                options = [ApplicationCommandOption.from_data(option_data) for option_data in option_datas]
            
            if self.options != options:
                old_attributes['options'] = self.options
                self.options = options
        
        try:
            allow_by_default = data['default_permission']
        except KeyError:
            pass
        else:
            if self.allow_by_default != self.allow_by_default:
                old_attributes['allow_by_default'] = allow_by_default
                self.allow_by_default = allow_by_default
        
        return old_attributes
    
    def to_data(self):
        """
        Converts the application command to a json serializable object.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        data = {
            'description': self.description,
            'name': self.name,
        }
    
        options = self.options
        if (options is not None):
            data['options'] = [option.to_data() for option in options]
        
        # Always add this to data, so if we update the command with it, will be always updated.
        data['default_permission'] = self.allow_by_default
        
        return data
    
    def __repr__(self):
        """Returns the application command's representation."""
        repr_parts = [
            '<', self.__class__.__name__,
        ]
        
        id_ = self.id
        if id_ == 0:
            repr_parts.append(' partial')
        else:
            repr_parts.append(' id=')
            repr_parts.append(repr(id_))
            repr_parts.append(', application_id=')
            repr_parts.append(repr(self.application_id))
        
        repr_parts.append(' name=')
        repr_parts.append(repr(self.name))
        repr_parts.append(', description=')
        repr_parts.append(repr(self.description))
        
        if not self.allow_by_default:
            repr_parts.append(', allow_by_default=False')
        
        options = self.options
        if (options is not None):
            repr_parts.append(', options=[')
            
            index = 0
            limit = len(options)
            
            while True:
                option = options[index]
                index += 1
                repr_parts.append(repr(option))
                
                if index == limit:
                    break
                
                repr_parts.append(', ')
                continue
            
            repr_parts.append(']')
        
        repr_parts.append('>')
        
        return ''.join(repr_parts)
    
    @property
    def partial(self):
        """
        Returns whether the application command is partial.
        
        Returns
        -------
        partial : `bool`
        """
        if self.id == 0:
            return True
        
        return False
    
    def __hash__(self):
        """Returns the application's hash value."""
        id_ = self.id
        if id_:
            return id_
        
        raise TypeError(f'Cannot hash partial {self.__class__.__name__} object.')
    
    @classmethod
    def _from_edit_data(cls, data, interaction_id, application_id):
        """
        Creates an application command with the given parameters after an application command edition took place.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Application command data returned by it's ``.to_data`` method.
        interaction_id : `int`
            The unique identifier number of the newly created application command.
        application_id : `int`
            The new application identifier number of the newly created application command.
        
        Returns
        -------
        self : ``ApplicationCommand``
            The newly created or updated application command.
        """
        try:
            self = APPLICATION_COMMANDS[interaction_id]
        except KeyError:
            self = object.__new__(cls)
            self.id = interaction_id
            self.application_id = application_id
            APPLICATION_COMMANDS[interaction_id] = self
            
            # Discord might not include attributes in edit data, so we will set them first to avoid unset attributes.
            self.description = ''
            self.name = ''
            self.options = None
        
        self._update_no_return(data)
        
        return self
    
    def copy(self):
        """
        Copies the ``ApplicationCommand`` instance.
        
        Returns
        -------
        new : ``ApplicationCommand``
            A copied new partial application command.
        """
        new = object.__new__(type(self))
        new.id = 0
        new.application_id = 0
        new.name = self.name
        new.description = self.description
        new.allow_by_default = self.allow_by_default
        
        options = self.options
        if (options is not None):
            options = [option.copy() for option in options]
        new.options = options
        
        return new
    
    def __eq__(self, other):
        """Returns whether the two application commands are equal."""
        if type(self) is not type(other):
            return NotImplemented
        
        # If both entity is not partial, leave instantly by comparing id.
        self_id = self.id
        other_id = other.id
        if self_id and other_id:
            if self_id == other_id:
                return True
            
            return False
        
        if self.name != other.name:
            return False
        
        if self.description != other.description:
            return False
        
        if self.allow_by_default != other.allow_by_default:
            return False
        
        if self.options != other.options:
            return False
        
        return True
    
    def __ne__(self, other):
        """Returns whether the two application commands are different."""
        if type(self) is not type(other):
            return NotImplemented
        
        self_id = self.id
        other_id = other.id
        if self_id and other_id:
            if self_id == other_id:
                return False
            
            return True
        
        if self.name != other.name:
            return True
        
        if self.description != other.description:
            return True
        
        if self.allow_by_default != other.allow_by_default:
            return True
        
        if self.options != other.options:
            return True
        
        return False
    
    @property
    def mention(self):
        """
        Returns the application command's mention.
        
        Returns
        -------
        mention : `str`
        """
        return f'</{self.name}:{self.id}>'
    
    @property
    def display_name(self):
        """
        Returns the application command's display name.
        
        Returns
        -------
        display_name : `str`
        """
        return self.name.lower().replace('_', '-')
    
    def __str__(self):
        """Returns the application command's name."""
        return self.name
    
    def __format__(self, code):
        """
        Formats the application command in a format string.
        
        Parameters
        ----------
        code : `str`
            The option on based the result will be formatted.
        
        Returns
        -------
        application_command : `str`
        
        Raises
        ------
        ValueError
            Unknown format code.
        
        Examples
        --------
        ```py
        >>> from hata import ApplicationCommand
        >>> application_command = ApplicationCommand('cake-lover', 'Sends a random cake recipe OwO')
        >>> application_command
        <ApplicationCommand partial name='cake-lover', description='Sends a random cake recipe OwO'>
        >>> # no code stands for str(application_command).
        >>> f'{application_command}'
        'CakeLover'
        >>> # 'd' stands for display name.
        >>> f'{application_command:d}'
        'cake-lover'
        >>> # 'm' stands for mention.
        >>> f'{application_command:m}'
        '</cake-lover:0>'
        >>> # 'c' stands for created at.
        >>> f'{application_command:c}'
        '2021-01-03 20:17:36'
        ```
        """
        if not code:
            return self.__str__()
        
        if code == 'm':
            return f'</{self.name}:{self.id}>'
        
        if code == 'd':
            return self.display_name
        
        if code == 'c':
            return self.created_at.__format__(DATETIME_FORMAT_CODE)
        
        raise ValueError(f'Unknown format code {code!r} for object of type {self.__class__.__name__!r}')
    
    def __len__(self):
        """Returns the application command's length."""
        length = len(self.name) + len(self.description)
        
        options = self.options
        if (options is not None):
            for option in options:
                length += len(option)
        
        return length


class ApplicationCommandOption:
    """
    An option of an ``ApplicationCommand``.
    
    Attributes
    ----------
    choices : `None` or `list` of ``ApplicationCommandOptionChoice``
        Choices for `str` and `int` types for the user to pick from.
    default : `bool`
        Whether the option is the default one. Only one option can be `default`.
    description : `str`
        The description of the application command option. It's length can be in range [1:100].
    name : `str`
        The name of the application command option. It's length can be in range [1:32].
    options : `None` or `list` of ``ApplicationCommandOption``
        If the command's type is sub-command group type, then this nested option will be the parameters of the
        sub-command. It's length can be in range [0:25]. If would be set as empty list, instead is set as `None`.
    required : `bool`
        Whether the parameter is required. Defaults to `False`.
    type : ``ApplicationCommandOptionType``
        The option's type.
    """
    __slots__ = ('choices', 'default', 'description', 'name', 'options', 'required', 'type')
    
    def __new__(cls, name, description, type_, *, default=False, required=False, choices=None, options=None):
        """
        Creates a new ``ApplicationCommandOption`` instance with the given parameters.
        
        Parameters
        ----------
        name : `str`
            The name of the command. It's length can be in range [1:32].
        description : `str`
            The command's description. It's length can be in range [2:100].
        type_ : `int` or ``ApplicationCommandOptionType``
            The application command option's type.
        default : `bool`, Optional (Keyword only)
            Whether the option is the default one. Defaults to `False`.
        required : `bool`, Optional (Keyword only)
            Whether the parameter is required. Defaults to `False`.
        choices : `None` or (`list` or `tuple`) of ``ApplicationCommandOptionChoice``, Optional (Keyword only)
            The choices of the command for string or integer types. It's length can be in range [0:25].
        options : `None` or (`list` or `tuple`) of ``ApplicationCommandOption``, Optional (Keyword only)
            The parameters of the command. It's length can be in range [0:25]. Only applicable for sub command groups.
        
        Raises
        ------
        TypeError
            - If `type_` was not given neither as `int` nor ``ApplicationCommandOptionType`` instance.
            - If `choices` was given meanwhile `type_` is neither string nor integer option type.
            - If `options` was given meanwhile `type_` is not a sub-command group option type.
            - If a choice's value's type not matched the expected type described `type_`.
        ValueError
            - If `type_` was given as `int` instance, but it do not matches any of the precreated
                ``ApplicationCommandOptionType``-s.
        AssertionError
            - If `name` was not given as `str` instance.
            - If `name` length is out of range [1:32].
            - If `description` was not given as `str` instance.
            - If `description` length is out of range [1:100].
            - If `options` was not given neither as `None` nor as (`list` or `tuple`) of ``ApplicationCommandOption``
                instances.
            - If `options`'s length is out of range [0:25].
            - If `default` was not given as `bool` instance.
            - If `required` was not given as `bool` instance.
            - If `choices` was not given neither as `None` nor as (`list` or `tuple`) of
                ``ApplicationCommandOptionChoice`` instances.
            - If `choices`'s length is out of range [0:25].
            - If an option is a sub command group option.
        """
        if __debug__:
            if not isinstance(name, str):
                raise AssertionError(f'`name` can be given as `str` instance, got {name.__class__.__name__}.')
            
            name_length = len(name)
            if name_length < APPLICATION_COMMAND_NAME_LENGTH_MIN or \
                    name_length > APPLICATION_COMMAND_NAME_LENGTH_MAX:
                raise AssertionError(f'`name` length can be in range '
                    f'[{APPLICATION_COMMAND_NAME_LENGTH_MIN}:{APPLICATION_COMMAND_NAME_LENGTH_MAX}], got '
                    f'{name_length!r}; {name!r}.')
        
            if not isinstance(description, str):
                raise AssertionError(f'`description` can be given as `str` instance, got '
                    f'{description.__class__.__name__}.')
            
            description_length = len(description)
            if description_length < APPLICATION_COMMAND_DESCRIPTION_LENGTH_MIN or \
                    description_length > APPLICATION_COMMAND_DESCRIPTION_LENGTH_MAX:
                raise AssertionError(f'`description` length can be in range '
                    f'[{APPLICATION_COMMAND_DESCRIPTION_LENGTH_MIN}:'
                    f'{APPLICATION_COMMAND_DESCRIPTION_LENGTH_MAX}], got {description_length!r}; '
                    f'{description!r}.')
        
        type_ = preconvert_preinstanced_type(type_, 'type_', ApplicationCommandOptionType)
        
        if __debug__:
            if not isinstance(default, bool):
                raise AssertionError(f'`default` can be given as `bool` instance, got {default.__class__.__name__}.')
            
            if not isinstance(required, bool):
                raise AssertionError(f'`required` can be given as `bool` instance, got {required.__class__.__name__}.')
        
        if choices is None:
            choices_processed = None
        else:
            if __debug__:
                if not isinstance(choices, (tuple, list)):
                    raise AssertionError(f'`choices` can be given as `None` or (`list` or `tuple`) of '
                        f'`{ApplicationCommandOptionChoice.__name__}`, got {choices.__class__.__name__}.')
            
            choices_processed = list(choices)
            
            if __debug__:
                if len(choices_processed) > APPLICATION_COMMAND_CHOICES_MAX:
                    raise AssertionError(f'`choices` length can be in range '
                        f'[0:{APPLICATION_COMMAND_CHOICES_MAX}], got {len(choices_processed)!r}; '
                        f'{choices!r}')
                
                for index, choice in enumerate(choices_processed):
                    if not isinstance(choice, ApplicationCommandOptionChoice):
                        raise AssertionError(f'`choices` was given either as `list` or `tuple`, but it\'s element '
                            f'At index {index!r} is not {ApplicationCommandOptionChoice.__name__} instance, but '
                            f'{choice.__class__.__name__}; got {choices!r}.')
            
            if not choices_processed:
                choices_processed = None
        
        if options is None:
            options_processed = None
        else:
            if __debug__:
                if not isinstance(options, (tuple, list)):
                    raise AssertionError(f'`options` can be given as `None` or (`list` or `tuple`) of '
                        f'`{ApplicationCommandOption.__name__}`, got {options.__class__.__name__}.')
            
            # Copy it
            options_processed = list(options)
            
            if __debug__:
                if len(options_processed) > APPLICATION_COMMAND_OPTIONS_MAX:
                    raise AssertionError(f'`options` length can be in range '
                        f'[0:{APPLICATION_COMMAND_OPTIONS_MAX}], got {len(options_processed)!r}; {options!r}')
                
                for index, option in enumerate(options_processed):
                    if not isinstance(option, ApplicationCommandOption):
                        raise AssertionError(f'`options` was given either as `list` or `tuple`, but it\'s element '
                            f'At index {index!r} is not {ApplicationCommandOption.__name__} instance, but '
                            f'{option.__class__.__name__}; got {options!r}.')
                    
                    if option.type is ApplicationCommandOptionType.sub_command_group:
                        raise AssertionError(f'`options` element {index}\'s type is cub-command group option, but'
                             f'sub-command groups cannot be added under sub-command groups; got {options!r}.')
            
            if not options_processed:
                options_processed = None
        
        if (choices_processed is not None):
            if type_ is ApplicationCommandOptionType.string:
                expected_choice_type = str
            elif type_ is ApplicationCommandOptionType.integer:
                expected_choice_type = int
            else:
                raise TypeError(f'`choices` is bound to string and integer option type, got choices={choices!r}, '
                    f'type={type_!r}.')
            
            for index, choice in enumerate(choices):
                if not isinstance(choice.value, expected_choice_type):
                    raise TypeError(f'`choices` element\'s {index!r} value\'s type is not '
                        f'`{expected_choice_type.__name__}` as expected from the received command option type: '
                        f'{type_!r}')
                pass
        
        self = object.__new__(cls)
        self.name = name
        self.description = description
        self.type = type_
        self.default = default
        self.required = required
        self.choices = choices_processed
        self.options = options_processed
        return self
    
    def add_option(self, option):
        """
        Adds a new option to the application command option.
        
        Parameters
        ----------
        option : ``ApplicationCommandOption``
            The option to add.
        
        Returns
        -------
        self : ``ApplicationCommandOption``
        
        Raises
        ------
        TypeError
            If the source application command's type is not a sub-command group type.
        AssertionError
            - If `option` is not ``ApplicationCommandOption`` instance.
            - If the ``ApplicationCommandOption`` has already `25` options.
            - If `option` is a sub command group option.
        """
        if self.type is not ApplicationCommandOptionType.sub_command_group:
            raise TypeError(f'`option` can be added only if the command option\s type is sub command option, '
                f'got option={option!r}, self={self!r}.')
        
        if __debug__:
            if not isinstance(option, ApplicationCommandOption):
                raise AssertionError(f'`option` can be given as {ApplicationCommandOption.__name__} instance, got '
                    f'{option.__class__.__name__}.')
        
            if option.type is ApplicationCommandOptionType.sub_command_group:
                raise AssertionError(f'`option`\'s type is sub-command group option, but sub-command groups cannot be '
                    f'added under sub-command groups; got {option!r}.')
        
        options = self.options
        if options is None:
            self.options = options = []
        else:
            if __debug__:
                if len(options) >= APPLICATION_COMMAND_OPTIONS_MAX:
                    raise AssertionError(f'`option` cannot be added if the {ApplicationCommandOption.__name__} has '
                        f'already `{APPLICATION_COMMAND_OPTIONS_MAX}` options.')
        
        options.append(option)
        return self
    
    def add_choice(self, choice):
        """
        Adds a ``ApplicationCommandOptionChoice`` to the application command option.
        
        Parameters
        ----------
        choice : ``ApplicationCommandOptionChoice`` or `tuple` (`str`, `str` or `int`)
            The choice to add.
        
        Returns
        -------
        self : ``ApplicationCommandOption``
        
        Raises
        ------
        TypeError
            - If the source application command's type is not a string nor int group type.
            - If the `choice`'s value's type is not the expected one by the command option's type.
            - If `choice`'s type is neither ``ApplicationCommandOptionChoice`` nor a `tuple` representing it's `.name`
                nad `.value`.
        AssertionError
            If the application command option has already `25` choices.
        """
        if isinstance(choice, ApplicationCommandOptionChoice):
            pass
        elif isinstance(choice, tuple):
            if len(choice) != 2:
                raise TypeError(f'If `choice` is given as `tuple` it\'s length should be `2` representing a '
                    f'{ApplicationCommandOptionChoice.__name__}\s `.name` and `.value`.')
            
            choice = ApplicationCommandOptionChoice(*choice)
        else:
            raise TypeError(f'`choice` can be given as {ApplicationCommandOptionChoice.__name__} instance or a `tuple` '
                f'representing one with i\'s respective `.name` and `.value` as it\'s elements, got '
                f'{choice.__class__.__name__}.')
        
        type_ = self.type
        if type_ is ApplicationCommandOptionType.string:
            expected_choice_type = str
        elif type_ is ApplicationCommandOptionType.integer:
            expected_choice_type = int
        else:
            raise TypeError(f'`choice` is bound to string and integer choice type, got choice={choice!r}, '
                f'self={self!r}.')
        
        if not isinstance(choice.value, expected_choice_type):
            raise TypeError(f'`choice` value\'s type is not `{expected_choice_type.__name__}` as expected from the '
                f'received command choice type: {type_!r}')
        
        choices = self.choices
        if choices is None:
            self.choices = choices = []
        else:
            if __debug__:
                if len(choices) >= APPLICATION_COMMAND_CHOICES_MAX:
                    raise AssertionError(f'`choice` cannot be added if the {ApplicationCommandOption.__name__} has '
                        f'already `{APPLICATION_COMMAND_CHOICES_MAX}` choices.')
        
        choices.append(choice)
        return self
    
    @classmethod
    def from_data(cls, data):
        """
        Creates a new ``ApplicationCommandOption`` instance from the received data from Discord.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Received application command option data.
        
        Returns
        -------
        self : ``ApplicationCommandOption``
            The created application command option.
        """
        self = object.__new__(cls)
        choice_datas = data.get('choices', None)
        if (choice_datas is None) or (not choice_datas):
            choices = None
        else:
            choices = [ApplicationCommandOptionChoice.from_data(choice_data) for choice_data in choice_datas]
        self.choices = choices
        
        self.default = data.get('default', False)
        self.description = data['description']
        self.name = data['name']
        
        option_datas = data.get('options', None)
        if (option_datas is None) or (not option_datas):
            options = None
        else:
            options = [ApplicationCommandOption.from_data(option_data) for option_data in option_datas]
        self.options = options
        
        self.required = data.get('required', False)
        
        self.type = ApplicationCommandOptionType.get(data['type'])
        return self
    
    def to_data(self):
        """
        Converts the application command option to a json serializable object.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        data = {
            'description' : self.description,
            'name' : self.name,
            'type' : self.type.value,
                }
        
        choices = self.choices
        if (choices is not None):
            data['choices'] = [choice.to_data() for choice in choices]
        
        
        if self.default:
            data['default'] = True
        
        options = self.options
        if (options is not None):
            data['options'] = [option.to_data() for option in options]
        
        if self.required:
            data['required'] = True
        
        return data
    
    def __repr__(self):
        """Returns the application command option's representation."""
        result = [
            '<', self.__class__.__name__,
            ', name=', repr(self.name),
            ', description=', repr(self.description),
            ', type=',
                ]
        
        type_ = self.type
        result.append(repr(type_.value))
        result.append(' (')
        result.append(type_.name)
        result.append(')')
        
        if self.default:
            result.append(', default=True')
        
        if self.required:
            result.append(', required=True')
        
        choices = self.choices
        if (choices is not None):
            result.append(', choices=[')
            
            index = 0
            limit = len(choices)
            
            while True:
                choice = choices[index]
                index += 1
                result.append(repr(choice))
                
                if index == limit:
                    break
                
                result.append(', ')
                continue
        
        options = self.options
        if (options is not None):
            result.append(', options=[')
            
            index = 0
            limit = len(options)
            
            while True:
                option = options[index]
                index += 1
                result.append(repr(option))
                
                if index == limit:
                    break
                
                result.append(', ')
                continue
            
            result.append(']')
        
        result.append('>')
        
        return ''.join(result)
    
    def copy(self):
        """
        Copies the ``ApplicationCommandOption``.
        
        Returns
        -------
        new : ``ApplicationCommandOption``
        """
        new = object.__new__(type(self))
        
        choices = self.choices
        if (choices is not None):
            choices = choices.copy()
        new.choices = choices
        
        new.default = self.default
        new.description = self.description
        new.name = self.name
        
        options = self.options
        if (options is not None):
            options = [option.copy() for option in options]
        new.options = options
        
        new.required = self.required
        new.type = self.type
        return new
    
    def __eq__(self, other):
        """Returns whether the two options are equal."""
        if type(self) is not type(other):
            return NotImplemented
        
        if self.choices != other.choices:
            return False
        
        if self.default != other.default:
            return False
        
        if self.description != other.description:
            return False
        
        if self.name != other.name:
            return False
        
        if self.options != other.options:
            return False
        
        if self.required != other.required:
            return False
        
        if self.type is not other.type:
            return False
        
        return True
    
    def __len__(self):
        """Returns the application command option's length."""
        length = len(self.name) + len(self.description)
        
        choices = self.choices
        if (choices is not None):
            for choice in choices:
                length += len(choice)
        
        options = self.options
        if (options is not None):
            for option in options:
                length += len(option)
        
        return length


class ApplicationCommandOptionChoice:
    """
    A choice of a ``ApplicationCommandOption``.
    
    Attributes
    ----------
    name : `str`
        The choice's name. It's length can be in range [1:100].
    value : `str` or `int`
        The choice's value.
    """
    __slots__ = ('name', 'value')
    
    def __new__(cls, name, value):
        """
        Creates a new ``ApplicationCommandOptionChoice`` instance with the given parameters.
        
        Parameters
        ----------
        name : `str`
            The choice's name. It's length can be in range [1:100].
        value : `str` or `int`
            The choice's value.
        
        Raises
        ------
        AssertionError
            - If `name` is not `str` instance.
            - If `name`'s length is out of range [1:100].
            - If `value` is neither `str` nor `int` instance.
            - If `value` is `str` and it's length is out of range [0:100].
        """
        if __debug__:
            if not isinstance(name, str):
                raise AssertionError(f'`name` can be given as `str` instance, got {name.__class__.__name__}.')
            
            name_length = len(name)
            if name_length < APPLICATION_COMMAND_CHOICE_NAME_LENGTH_MIN or \
                    name_length > APPLICATION_COMMAND_CHOICE_NAME_LENGTH_MAX:
                raise AssertionError(f'`name` length can be in range '
                    f'[{APPLICATION_COMMAND_CHOICE_NAME_LENGTH_MIN}:{APPLICATION_COMMAND_CHOICE_NAME_LENGTH_MAX}], '
                    f'got {name_length!r}; {name!r}.')
            
            if isinstance(value, int):
                pass
            elif isinstance(value, str):
                value_length = len(value)
                if value_length < APPLICATION_COMMAND_CHOICE_VALUE_LENGTH_MIN or \
                        value_length > APPLICATION_COMMAND_CHOICE_VALUE_LENGTH_MAX:
                    raise AssertionError(f'`value` length` can be in range '
                        f'[{APPLICATION_COMMAND_CHOICE_VALUE_LENGTH_MIN}:{APPLICATION_COMMAND_CHOICE_NAME_LENGTH_MAX}]'
                        f'got {value_length!r}; {value!r}.')
            else:
                raise AssertionError(f'`value` type can be either `str` or `int`, got {value.__class__.__name__}.')
        
        self = object.__new__(cls)
        self.name = name
        self.value = value
        return self
    
    @classmethod
    def from_data(cls, data):
        """
        Creates a new ``ApplicationCommandOptionChoice`` instance from the received data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            The received application command option choice data.
        
        Returns
        -------
        self : ``ApplicationCommandOptionChoice``
            The created choice.
        """
        self = object.__new__(cls)
        self.name = data['name']
        self.value = data['value']
        return self
    
    def to_data(self):
        """
        Converts the application command option choice to a json serializable object.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        return {
            'name' : self.name,
            'value' : self.value,
                }
    
    def __repr__(self):
        """Returns the application command option choice's representation."""
        return f'<{self.__class__.__name__} name={self.name!r}, value={self.value!r}>'
    
    def __eq__(self, other):
        """Returns whether the two choices are equal."""
        if type(self) is not type(other):
            return NotImplemented
        
        if self.name != other.name:
            return False
        
        if self.value != other.value:
            return False
        
        return True
    
    def __len__(self):
        """Returns the application command choice's length."""
        length = len(self.name)
        value = self.value
        if isinstance(value, str):
            length += len(value)
        
        return length


class ApplicationCommandPermission:
    """
    Stores am ``ApplicationCommand``'s overwrites.
    
    Attributes
    ----------
    application_command_id : `int`
        The identifier of the respective ``ApplicationCommand``.
    application_id : `int`
        The application command's application's identifier.
    guild_id : `int`
        The identifier of the respective guild.
    overwrites : `None` or `list` of ``ApplicationCommandPermissionOverwrite``
        The application command overwrites relating to the respective application command in the guild.
    """
    __slots__ = ('application_command_id', 'application_id', 'guild_id', 'overwrites')
    
    def __new__(cls, application_command, *, overwrites=None):
        """
        Creates a new ``ApplicationCommandPermission`` instance from the given parameters.
        
        Parameters
        ----------
        application_command : ``ApplicationCommand`` or `int`
            The application command's identifier.
        overwrites : `None` or (`list`, `set`, `tuple`) of ``ApplicationCommandPermissionOverwrite`
                , Optional (Keyword only)
            Overwrites for the application command.
        
        Raises
        ------
        TypeError
            - If `application_command` was not given neither as ``ApplicationCommand`` nor as `int` instance.
        AssertionError
            - If `overwrites` was not give neither as `None`, `list`, `set` or `tuple`.
            - If `overwrites` contains a non ``ApplicationCommandPermissionOverwrite`` element.
            - If `overwrites` length is over `10`.
        """
        if isinstance(application_command, ApplicationCommand):
            application_command_id = application_command.id
        else:
            application_command_id = maybe_snowflake(application_command)
            if application_command_id is None:
                raise TypeError(f'`application_command` can be given as `{ApplicationCommand.__name__}`, or as `int` '
                    f'instance, got {application_command.__class__.__name__}.')
        
        if overwrites is None:
            overwrites_processed = None
        else:
            if __debug__:
                if not isinstance(overwrites, (list, set, tuple)):
                    raise AssertionError(f'`overwrites` can be given either as `None` or as `list`, `set`, `tuple`'
                         f'instance, got {overwrites.__class__.__name__}.')
            
            overwrites_processed = []
            
            for overwrite in overwrites:
                if __debug__:
                    if not isinstance(overwrite, ApplicationCommandPermissionOverwrite):
                        raise AssertionError(f'`overwrites` contains a non '
                            f'{ApplicationCommandPermissionOverwrite.__name__} element, got '
                            f'{overwrite.__class__.__name__}.')
                
                overwrites_processed.append(overwrite)
                
            
            if overwrites_processed:
                if __debug__:
                    if len(overwrites) >= APPLICATION_COMMAND_PERMISSION_OVERWRITE_MAX:
                        raise AssertionError(f'`overwrites` can contain up to '
                            f'`{APPLICATION_COMMAND_PERMISSION_OVERWRITE_MAX}` overwrites, which is passed, got '
                            f'{len(overwrites)!r}.')
            else:
                overwrites_processed = None
        
        self = object.__new__(cls)
        self.application_command_id = application_command_id
        self.application_id = 0
        self.guild_id = 0
        self.overwrites = overwrites_processed
        return self
    
    @classmethod
    def from_data(cls, data):
        """
        Creates a new ``ApplicationCommandPermission`` instance.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Application command data.
        
        Returns
        -------
        self : ``ApplicationCommandPermission``
        """
        overwrite_datas = data['permissions']
        if overwrite_datas:
            overwrites = [ApplicationCommandPermissionOverwrite.from_data(overwrite_data) for \
                overwrite_data in overwrite_datas]
            
        else:
            overwrites = None
        
        self = object.__new__(cls)
        self.application_command_id = int(data['id'])
        self.application_id = int(data['application_id'])
        self.guild_id = int(data['guild_id'])
        self.overwrites = overwrites
        return self
    
    def to_data(self):
        """
        Converts the application command permission to a json serializable object.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        data = {
            'id' : self.application_command_id,
            'application_id' : self.application_id,
            'guild_id' : self.guild_id,
        }
        
        overwrites = self.overwrites
        if overwrites is None:
            overwrites = []
        else:
            overwrites = [overwrite.to_data() for overwrite in overwrites]
        
        data['permissions'] = overwrites
        
        return data
    
    def __repr__(self):
        """Returns the application command permission's representation."""
        result = ['<', self.__class__.__name__, ' application_command_id=', repr(self.application_command_id),
            ' guild_id=', repr(self.guild_id), ', overwrite count=']
        
        overwrites = self.overwrites
        if overwrites is None:
            overwrites_count = '0'
        else:
            overwrites_count = repr(len(overwrites))
        
        result.append(overwrites_count)
        result.append('>')
        
        return ''.join(result)
    
    def __eq__(self, other):
        """Returns whether the two application command permission's are equal."""
        if type(self) is not type(other):
            return NotImplemented
        
        # No need to compare application_id, since `application_command_id` are already unique.
        if self.application_command_id != other.application_command_id:
            return False
        
        if self.guild_id != other.guild_id:
            return False
        
        if self.overwrites != other.overwrites:
            return False
        
        return True
    
    def __hash__(self):
        """Returns the application command overwrite's hash value."""
        hash_ = self.application_command_id ^ self.guild_id
        overwrites = self.overwrites
        if (overwrites is not None):
            for overwrite in overwrites:
                hash_ ^= hash(overwrite)
        
        return hash_
    
    def copy(self):
        """
        Copies the application command permission.
        
        Returns
        -------
        new : ``ApplicationCommandPermission``
        """
        new = object.__new__(type(self))
        
        new.application_id = self.application_id
        new.application_command_id = self.application_command_id
        new.guild_id = self.guild_id
        
        overwrites = self.overwrites
        if (overwrites is not None):
            overwrites = [overwrite.copy() for overwrite in overwrites]
        
        new.overwrites = overwrites
        
        return new
    
    def add_overwrite(self, overwrite):
        """
        Adds an application command permission overwrite to the overwrites of the application command permission.
        
        Parameters
        ----------
        overwrite : ``ApplicationCommandPermissionOverwrite``
            The overwrite to add.
        
        Raises
        ------
        AssertionError
            - If `overwrite` is not ``ApplicationCommandPermissionOverwrite`` instance.
            - If the application command permission has `10` overwrites already.
        """
        if __debug__:
            if not isinstance(overwrite, ApplicationCommandPermissionOverwrite):
                raise AssertionError(f'`overwrite` can be given as {ApplicationCommandPermissionOverwrite.__name__} '
                    f' instance, got {overwrite.__class__.__name__}.')
        
        overwrites = self.overwrites
        if overwrites is None:
            self.overwrites = overwrites = []
        else:
            if __debug__:
                if len(overwrites) >= APPLICATION_COMMAND_PERMISSION_OVERWRITE_MAX:
                    raise AssertionError(f'`overwrites` can contain up to '
                        f'`{APPLICATION_COMMAND_PERMISSION_OVERWRITE_MAX}` overwrites, which is already reached.')
        
        overwrites.append(overwrite)


class ApplicationCommandPermissionOverwrite:
    """
    Represents an application command's allow/disallow overwrite for the given entity.
    
    Attributes
    ----------
    allow : `bool`
        Whether the respective command is allowed for the represented entity.
    target_id : `int`
        The represented entity's identifier.
    type : ``ApplicationCommandPermissionOverwriteType`
        The target entity's type.
    """
    def __new__(cls, target, allow):
        """
        Creates a new ``ApplicationCommandPermission`` instance with the given parameters.
        
        Parameters
        ----------
        target : ``ClientUserBase`` or ``Role``, `tuple` ((``ClientUserBase``, ``Role`` type) or \
                `str` (`'Role'`, `'role'`, `'User'`, `'user'`), `int`)
            The target entity of the application command permission overwrite.
            
            The expected type & value might be pretty confusing, but the target was it to allow relaxing creation.
            To avoid confusing, here is a list of the expected structures:
            
            - ``Role`` instance
            - ``ClientUserBase`` instance
            - `tuple` (``Role`` type, `int`)
            - `tuple` (``ClientUserBase`` instance, `int`)
            - `tuple` (`'Role'`, `int`)
            - `tuple` (`'role'`, `int`)
            - `tuple` (`'User'`, `int`)
            - `tuple` (`'user'`, `int`)
        
        allow : `bool`
            Whether the respective application command should be enabled for the respective entity.
        
        Raises
        ------
        TypeError
            If `target` was not given as any of the expected types & values.
        AssertionError
            If `allow` was not given as `bool` instance.
        """
        # GOTO
        while True:
            if isinstance(target, Role):
                type_ = APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_ROLE
                target_id = target.id
                target_lookup_failed = False
                break
            
            if isinstance(target, ClientUserBase):
                type_ = APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_USER
                target_id = target.id
                target_lookup_failed = False
                break
            
            if isinstance(target, tuple) and len(target) == 2:
                target_type_maybe, target_id_maybe = target
                
                if isinstance(target_type_maybe, type):
                    if issubclass(target_type_maybe, Role):
                        type_ = APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_ROLE
                    elif issubclass(target_type_maybe, ClientUserBase):
                        type_ = APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_USER
                    else:
                        target_lookup_failed = True
                        break
                
                elif isinstance(target_type_maybe, str):
                    if target_type_maybe in ('Role', 'role'):
                        type_ = APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_ROLE
                    elif target_type_maybe in ('User', 'user'):
                        type_ = APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_USER
                    else:
                        target_lookup_failed = True
                        break
                
                else:
                    target_lookup_failed = True
                    break
                
                if type(target_id_maybe) is int:
                    target_id = target_id_maybe
                elif isinstance(target_id_maybe, int):
                    target_id = int(target_id_maybe)
                else:
                    target_lookup_failed = True
                    break
                
                target_lookup_failed = False
                break
            
            target_lookup_failed = True
            break
        
        if target_lookup_failed:
            raise TypeError(f'`target` can be given either as {Role.__name__}, {ClientUserBase.__name__}, '
                f'or as a `tuple` (({Role.__name__}, {User.__name__}, {UserBase.__name__} type or `str` '
                f'(`\'Role\'`, `\'role\'`, `\'User\'`, `\'user\'`)), `int`), got {target.__class__.__name__}: '
                f'{target!r}.')
        
        if __debug__:
            if not isinstance(allow, bool):
                raise AssertionError(f'`allow` can be given as `bool` instance, got {allow.__class__.__name__}.')
        
        self = object.__new__(cls)
        self.allow = allow
        self.target_id = target_id
        self.type = type_
        return self
    
    @classmethod
    def from_data(cls, data):
        """
        Creates a new ``ApplicationCommandPermissionOverwrite`` instance from the received data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            The received application command permission overwrite data.
        
        Returns
        -------
        self : ``ApplicationCommandPermission``
            The created application command option.
        """
        self = object.__new__(cls)
        self.allow = data['permission']
        self.target_id = int(data['id'])
        self.type = ApplicationCommandPermissionOverwriteType.get(data['type'])
        return self
    
    def to_data(self):
        """
        Converts the application command permission overwrite to a json serializable object.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        return {
            'permission': self.allow,
            'id': self.target_id,
            'type': self.type.value,
        }
    
    @property
    def target(self):
        """
        Returns the application command overwrite's target entity.
        
        Returns
        -------
        target : ``Role``, ``ClientUserBase``
        """
        type_ = self.type
        target_id = self.target_id
        if type_ is APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_ROLE:
            target = Role.precreate(target_id)
        else: # type_ is APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_USER:
            target = User.precreate(target_id)
        
        return target
    
    def __repr__(self):
        """Returns the application command permission overwrite's representation."""
        return f'<{self.__class__.__name__} type={self.type.name}, target_id={self.target_id!r}, allow={self.allow!r}>'
    
    def __eq__(self, other):
        """Returns whether the two application command overwrites are equal."""
        if type(self) is not type(other):
            return NotImplemented
        
        if self.allow != other.allow:
            return False
        
        if self.type is not other.type:
            return False
        
        if self.target_id != other.target_id:
            return False
        
        return True
    
    def __hash__(self):
        """Returns the application command permission overwrite's hash value."""
        hash_ = self.application_command_id ^ self.guild_id
        overwrites = self.overwrites
        if (overwrites is not None):
            for overwrite in overwrites:
                hash_ ^= hash(overwrite)
        
        return hash_
    
    def copy(self):
        """
        Copies the application command permission overwrite.
        
        Returns
        -------
        new : ``ApplicationCommandPermissionOverwrite``
        """
        new = object.__new__(type(self))
        
        new.allow = self.allow
        new.type = self.type
        new.target_id = self.target_id
        
        return new
    
    def __gt__(self, other):
        """Returns whether self is greater than other."""
        if type(self) is not type(other):
            return NotImplemented
        
        self_type_value = self.type.value
        other_type_value = other.type.value
        
        if self_type_value > other_type_value:
            return True
        
        if self_type_value < other_type_value:
            return False
        
        if self_type_value == APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_ROLE:
            self_target_id = self.target_id
            other_target_id = other.target_id
            
            self_role = ROLES.get(self_target_id, None)
            other_role = ROLES.get(other_target_id, None)
            if self_role is None:
                if other_role is None:
                    return (self_target_id > other_target_id)
                else:
                    return False
            else:
                if other_role is None:
                    return True
                else:
                    return (self_role > other_role)
        
        if self_type_value == APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_USER:
            return (self.target_id > other.target_id)
        
        # Should not happen
        return False

    def __lt__(self, other):
        """Returns whether self is greater than other."""
        if type(self) is not type(other):
            return NotImplemented
        
        self_type_value = self.type.value
        other_type_value = other.type.value
        
        if self_type_value > other_type_value:
            return False
        
        if self_type_value < other_type_value:
            return True
        
        if self_type_value == APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_ROLE:
            self_target_id = self.target_id
            other_target_id = other.target_id
            
            self_role = ROLES.get(self_target_id, None)
            other_role = ROLES.get(other_target_id, None)
            if self_role is None:
                if other_role is None:
                    return (self_target_id < other_target_id)
                else:
                    return True
            else:
                if other_role is None:
                    return False
                else:
                    return (self_role < other_role)
        
        if self_type_value == APPLICATION_COMMAND_PERMISSION_OVERWRITE_TYPE_USER:
            return (self.target_id < other.target_id)
        
        # Should not happen
        return True


@modulize
class InteractionResponseTypes:
    """
    Contains the interaction response type's, which are the following:
    
    +-----------------------+-------+---------------+
    | Respective name       | Value | Notes         |
    +=======================+=======+===============+
    | none                  | 0     | -             |
    +-----------------------+-------+---------------+
    | pong                  | 1     | -             |
    +-----------------------+-------+---------------+
    | acknowledge           | 2     | Deprecated.   |
    +-----------------------+-------+---------------+
    | message               | 3     | Deprecated.   |
    +-----------------------+-------+---------------+
    | message_and_source    | 4     | -             |
    +-----------------------+-------+---------------+
    | source                | 5     | -             |
    +-----------------------+-------+---------------+
    | component             | 6     | -             |
    +-----------------------+-------+---------------+
    """
    none = 0
    pong = 1
    acknowledge = 2
    message = 3
    message_and_source = 4
    source = 5
    component = 6


class ApplicationCommandInteraction(DiscordEntity):
    """
    Represents an ``ApplicationCommand`` invoked by a user.
    
    Attributes
    ----------
    id : `int`
        The represented application command's identifier number.
    name : `str`
        The name of the command. It's length can be in range [1:32].
    options : `None` or `list` of ApplicationCommandInteractionOption
        The parameters and values from the user if any. Defaults to `None` if non is received.
    resolved_channels : `None` or `dict` of (`int`, ``ChannelBase``) items
        Resolved received channels stored by their identifier as keys if any.
    resolved_roles : `None` or `dict` of (`int`, ``Role``) items
        Resolved received roles stored by their identifier as keys if any.
    resolved_users : `None` or `dict` of (`int`, ``ClientUserBase``) items
        Resolved received users stored by their identifier as keys if any.
    """
    __slots__ = ('name', 'options', 'resolved_channels', 'resolved_roles', 'resolved_users')
    def __new__(cls, data, guild, cached_users):
        """
        Creates a new ``ApplicationCommandInteraction`` from the data received from Discord.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            The received application command interaction data.
        guild : `None` or ``Guild``
            The respective guild.
        cached_users : `None` or `list` of ``ClientUserBase``
            Users, which might need temporary caching.
        
        Returns
        -------
        self : ``ApplicationCommandInteraction``
            The created object.
        cached_users : `None` or `list` of ``ClientUserBase``
            Users, which might need temporary caching.
        """
        try:
            resolved_data = data['resolved']
        except KeyError:
            resolved_users = None
            resolved_channels = None
            resolved_roles = None
        else:
            try:
                resolved_user_datas = resolved_data['users']
            except KeyError:
                resolved_users = None
            else:
                if resolved_user_datas:
                    try:
                        resolved_guild_profile_datas = resolved_data['members']
                    except KeyError:
                        resolved_guild_profile_datas = None
                    
                    resolved_users = {}
                    
                    for user_id, user_data in resolved_user_datas.items():
                        if resolved_guild_profile_datas is None:
                            guild_profile_data = None
                        else:
                            guild_profile_data = resolved_guild_profile_datas.get(user_id, None)
                        
                        if (guild_profile_data is not None):
                            user_data['member'] = guild_profile_data
                        
                        user = User(user_data, guild)
                        resolved_users[user.id] = user
                        
                        if (guild_profile_data is not None) and (cached_users is not None) and \
                                (user not in cached_users):
                            cached_users.append(user)
                    
                else:
                    resolved_users = None
            
            try:
                resolved_channel_datas = resolved_data['channels']
            except KeyError:
                resolved_channels = None
            else:
                if resolved_channel_datas:
                    resolved_channels = {}
                    
                    for channel_data in resolved_channel_datas.values():
                        channel = create_partial_channel(channel_data, guild)
                        if (channel is not None):
                            resolved_channels[channel.id] = channel
                    
                    if not resolved_channels:
                        resolved_channels = None
                else:
                    resolved_channels = None
            
            try:
                resolved_role_datas = resolved_data['roles']
            except KeyError:
                resolved_roles = None
            else:
                if resolved_role_datas:
                    resolved_roles = {}
                    for role_data in resolved_role_datas.values():
                        role = Role(role_data, guild)
                        resolved_roles[role.id] = role
                else:
                    resolved_roles = None
        
        id_ = int(data['id'])
        name = data['name']
        
        option_datas = data.get('options', None)
        if (option_datas is None) or (not option_datas):
            options = None
        else:
            options = [ApplicationCommandInteractionOption(option_data) for option_data in option_datas]
        
        self = object.__new__(cls)
        self.id = id_
        self.name = name
        self.options = options
        self.resolved_users = resolved_users
        self.resolved_channels = resolved_channels
        self.resolved_roles = resolved_roles
        
        return self, cached_users
    
    def __repr__(self):
        """Returns the application command interaction's representation."""
        result = [
            '<', self.__class__.__name__,
            ' id=', repr(self.id),
            ', name=', repr(self.name),
                ]
        
        options = self.options
        if (options is not None):
            result.append(', options=[')
            
            index = 0
            limit = len(options)
            
            while True:
                option = options[index]
                index += 1
                result.append(repr(option))
                
                if index == limit:
                    break
                
                result.append(', ')
                continue
            
            result.append(']')
        
        result.append('>')
        
        return ''.join(result)


class ApplicationCommandInteractionOption:
    """
    Represents an option of a ``ApplicationCommandInteraction``.
    
    Attributes
    ----------
    name : `str`
        The option's name.
    options : `None` or `list` of ``ApplicationCommandInteractionOption``
        The parameters and values from the user. Present if a sub-command was used. Defaults to `None` if non is
        received.
        
        Mutually exclusive with the `value` attribute.
    type : ``ApplicationCommandOptionType``
        The option's type.
    value : `None`, `str`
        The given value by the user. Should be always converted to the expected type.
    """
    __slots__ = ('name', 'options', 'type', 'value')
    def __new__(cls, data):
        """
        Creates a new ``ApplicationCommandInteractionOption`` instance from the data received from Discord.
        
        Attributes
        ----------
        data : `dict` of (`str`, `Any`) items
            The received application command interaction option data.
        """
        name = data['name']
        
        option_datas = data.get('options', None)
        if (option_datas is None) or (not option_datas):
            options = None
        else:
            options = [ApplicationCommandInteractionOption(option_data) for option_data in option_datas]
        
        self = object.__new__(cls)
        self.name = name
        self.options = options
        self.type = ApplicationCommandOptionType.get(data.get('type', 0))
        
        value = data.get('value', None)
        if value is not None:
            value = str(value)
        
        self.value = value
        
        return self
    
    def __repr__(self):
        """Returns the application command interaction option's representation."""
        repr_parts = [
            '<', self.__class__.__name__,
            ', name=', repr(self.name),
        ]
        
        type_ = self.type
        if type_ is not ApplicationCommandOptionType.none:
            repr_parts.append('type=')
            repr_parts.append(type_.name)
            repr_parts.append(' (')
            repr_parts.append(repr(type_.value))
            repr_parts.append(')')
        
        options = self.options
        if (options is not None):
            repr_parts.append(', options=[')
            
            index = 0
            limit = len(options)
            
            while True:
                option = options[index]
                index += 1
                repr_parts.append(repr(option))
                
                if index == limit:
                    break
                
                repr_parts.append(', ')
                continue
            
            repr_parts.append(']')
        
        value = self.value
        if (value is not None):
            repr_parts.append(', value=')
            repr_parts.append(repr(value))
        
        repr_parts.append('>')
        
        return ''.join(repr_parts)


@export
class ComponentBase:
    """
    Base class for 3rd party components.
    
    Class attributes
    ----------------
    custom_id : `None` or `str`, Optional (Keyword only)
        Custom identifier to detect which button was clicked by the user.
    type : ``ComponentType`` = `ComponentType.none`
        The component's type.
    """
    __slots__ = ()
    
    custom_id = None
    type = ComponentType.none
    
    @classmethod
    def from_data(cls, data):
        """
        Creates a new message component from the received data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Message component data.
        
        Returns
        -------
        self : ``ComponentBase`` instance
            The created component instance.
        """
        return None
    
    
    def to_data(self):
        """
        Converts the component to json serializable object.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        data = {
            'type' : self.type.value
        }
        
        return data
    
    
    def __repr__(self):
        """Returns the message component's representation."""
        return f'<{self.__class__.__name__}>'
    
    
    def copy(self):
        """
        Copies the component.
        
        Returns
        -------
        new : ``ComponentBase``
        """
        return None
    
    
    def __eq__(self, other):
        """Returns Whether the two component are equal."""
        if type(other) is not type(self):
            return NotImplemented
        
        return True
    
    
    def __hash__(self):
        """Returns the component's hash value."""
        return self.type.value


def _debug_component_components(components):
    """
    Checks whether given `component.components` value is correct.
    
    Parameters
    ----------
    components : `None` or (`list`, `tuple`) of ``ComponentBase``
        Sub-components.
    
    Raises
    ------
    AssertionError
        - If `components`'s length is out of the expected range [0:5].
        - If `components` is neither `None`, `tuple` or `list`.
        - If `components` contains a non ``Component`` instance.
    """
    if (components is None):
        pass
    elif isinstance(components, (tuple, list)):
        if (components is not None) and (len(components) > COMPONENT_SUB_COMPONENT_LIMIT):
            raise AssertionError(f'A `component.components` can have maximum 5 sub-components, got '
                f'{len(components)}; {components!r}.')
        
        for component in components:
            if not isinstance(component, ComponentBase):
                raise AssertionError(f'`component` can be given as `{ComponentBase.__name__}` instance, got '
                    f'{component.__class__.__name__}.')
            
            if component.type is COMPONENT_TYPE_ACTION_ROW:
                raise AssertionError(f'Cannot add `{COMPONENT_TYPE_ACTION_ROW}` type as sub components, got '
                    f'{component!r}.')
    else:
        raise AssertionError(f'`components` can be given as `None`, `tuple` or `list`, got '
            f'{components.__class__.__name__}.')


def _debug_component_custom_id(custom_id):
    """
    Checks whether given `component.custom_id` value is correct.
    
    Parameters
    ----------
    custom_id : `None` or `str`
        Custom identifier to detect which button was clicked by the user.
    
    Raises
    ------
    AssertionError
        - If `custom_id` was not given neither as `None` or `str` instance.
        - If `custom_id`'s length is over `100`.
    """
    if (custom_id is None):
        pass
    elif isinstance(custom_id, str):
        if len(custom_id) > COMPONENT_CUSTOM_ID_LENGTH_MAX:
            raise AssertionError(f'`custom_id`\'s max length can be {COMPONENT_CUSTOM_ID_LENGTH_MAX!r}, got '
                f'{len(custom_id)!r}; {custom_id!r}.')
    else:
        raise AssertionError(f'`custom_id` can be given either as `None` or as `str` instance, got '
            f'{custom_id.__class__.__name__}.')


def _debug_component_emoji(emoji):
    """
    Checks whether the given `component.emoji` value is correct.
    
    Parameters
    ----------
    emoji : `None` or ``Emoji``
        Emoji of the button if applicable.
    
    Raises
    ------
    AssertionError
        -If `emoji` was not given as ``Emoji`` instance.
    """
    if emoji is None:
        pass
    elif isinstance(emoji, Emoji):
        pass
    else:
        raise AssertionError(f'`emoji` can be given as `{Emoji.__name__}` instance, got '
            f'{emoji.__class__.__name__}')


def _debug_component_label(label):
    """
    Checks whether the given `component.label` value is correct.
    
    Parameters
    ----------
    label : `None` or `str`
        Label of the component.
    
    Raises
    ------
    AssertionError
        - If `label` was not given neither as `None` nor as `int` instance.
        - If `label`'s length is over `80`.
    """
    if label is None:
        pass
    elif isinstance(label, str):
        if len(label) > COMPONENT_LABEL_LENGTH_MAX:
            raise AssertionError(f'`label`\'s max length can be {COMPONENT_LABEL_LENGTH_MAX!r}, got '
                f'{len(label)!r}; {label!r}.')
    else:
        raise AssertionError(f'`label` can be given either as `None` or as `str` instance, got '
            f'{label.__class__.__name__}.')


def _debug_component_enabled(enabled):
    """
    Checks whether the given `component.enabled` value is correct.
    
    Parameters
    ----------
    enabled : `bool`
        Whether the button is enabled.
    
    Raises
    ------
    - If `enabled` was not given as `bool` instance.
    """
    if not isinstance(enabled, bool):
        raise AssertionError(f'`enabled` can be given as `bool` instance, got {enabled.__class__.__name__}.')


def _debug_component_url(url):
    """
    Checks whether the given `component.url` value is correct.
    
    Parameters
    ----------
    url : `None` or `str`
        Url to redirect to when clicking on a button.
    
    Raises
    ------
    AssertionError
        - If `url` was not given neither as `None` or `str` instance.
    """
    if url is None:
        pass
    elif isinstance(url, str):
        pass
    else:
        raise AssertionError(f'`url` can be given either as `None` or as `str` instance, got '
            f'{url.__class__.__name__}.')


@export
class Component(ComponentBase):
    """
    Message component! Aka buttons!
    
    Attributes
    ----------
    components : `None` or `list` of ``Component``
        Sub-components.
    custom_id : `None` or `str`
        Custom identifier to detect which button was clicked by the user.
        
        > Mutually exclusive with the `url` field.
    enabled : `bool`
        Whether the component is enabled.
    emoji : `None` or ``Emoji``
        Emoji of the button if applicable.
    label : `None` or `str`
        Label of the component.
    type : ``ComponentType``
        The component's type.
    style : `None` or ``ButtonStyle``
        The components's style. Applicable for buttons.
    url : `None` or `str`
        Url to redirect to when clicking on the button.
        
        > Mutually exclusive with the `custom_id` field.
    """
    __slots__ = ('components', 'custom_id', 'enabled', 'emoji', 'label', 'style', 'type', 'url',)
    
    def __new__(cls, type_, *, components=None, custom_id=None, emoji=None, label=None, style=None, url=None,
            enabled=True):
        """
        Creates a new component instance with the given parameters.
        
        Parameters
        ----------
        type : ``ComponentType``, `int`
            The component's type.
        components : `None` or (`list`, `tuple`) of ``ComponentBase``, Optional (Keyword only)
            Sub-components.
        custom_id : `None` or `str`, Optional (Keyword only)
            Custom identifier to detect which button was clicked by the user.
            
            > Mutually exclusive with the `url` field.
    
        emoji : `None` or ``Emoji``, Optional (Keyword only)
            Emoji of the button if applicable.
        style : ``ButtonStyle``, `int`, Optional (Keyword only)
            The components's style. Applicable for buttons.
        url : `None` or `str`, Optional (Keyword only)
            Url to redirect to when clicking on the button.
            
            > Mutually exclusive with the `custom_id` field.
        label : `None` or `str`, Optional (Keyword only)
            Label of the component.
        enabled : `bool`, Optional (Keyword only)
            Whether the button is enabled. Defaults to `True`.
        
        Raises
        ------
        TypeError
            - If `type` was not given neither as ``ComponentType`` not `int` instance.
            - If `style`'s type is unexpected.
        AssertionError
            - If `components` is neither `None`, `tuple` or `list`.
            - If `components` contains a non ``Component`` instance.
            - If `custom_id` was not given neither as `None` or `str` instance.
            - `url` is mutually exclusive with `custom_id`.
            - If `emoji` was not given as ``Emoji`` instance.
            - If `url` was not given neither as `None` or `str` instance.
            - If `style` was not given as any of the `type`'s expected styles.
            - If `type` is button type then `style` is required.
            - If `components`'s length is out of the expected range [0:5].
            - If an action row type component would be added as a sub-component.
            - If `label` was not given neither as `None` nor as `int` instance.
            - If `enabled` was not given as `bool` instance.
            - If `label`'s length is over `80`.
            - If `custom_id`'s length is over `100`.
        """
        if __debug__:
            _debug_component_components(components)
            _debug_component_custom_id(custom_id)
            _debug_component_emoji(emoji)
            _debug_component_label(label)
            _debug_component_enabled(enabled)
            _debug_component_url(url)
            
            if (custom_id is not None) and (url is not None):
                raise AssertionError(f'`custom_id` and `url` fields are mutually exclusive, got '
                    f'custom_id={custom_id!r}, url={url!r}.')
        
        type_ = preconvert_preinstanced_type(type_, 'type_', ComponentType)
        
        component_style_type = COMPONENT_TYPE_TO_STYLE.get(type_, None)
        if component_style_type is None:
            style = None
        else:
            style = preconvert_preinstanced_type(style, 'style', component_style_type)
        
        components_processed = None
        if (components is not None):
            for component in components:
                if components_processed is None:
                    components_processed = []
                
                components_processed.append(component)
        
        if (label is not None) and (not label):
            label = None
        
        self = object.__new__(cls)
        
        self.type = type_
        self.style = style
        self.components = components_processed
        self.custom_id = custom_id
        self.emoji = emoji
        self.url = url
        self.label = label
        self.enabled = enbaled
        
        return self
    
    
    @classmethod
    @copy_docs(ComponentBase.from_data)
    def from_data(cls, data):
        self = object.__new__(cls)
        
        self.type = ComponentType.get(data['type'])
        
        emoji_data = data.get('emoji', None)
        if emoji_data is None:
            emoji = None
        else:
            emoji = create_partial_emoji(emoji_data)
        self.emoji = emoji
        
        component_datas = data.get('components', None)
        if (component_datas is None) or (not component_datas):
            components = None
        else:
            components = [Component.from_data(component_data) for component_data in component_datas]
        self.components = components
        
        style = data.get('style', None)
        if (style is not None):
            style = ButtonStyle.get(style)
        self.style = style
        
        self.url = data.get('url', None)
        
        self.custom_id = data.get('custom_id', None)
        
        self.label = data.get('label', None)
        
        self.enabled = not data.get('disabled', False)
        
        return self
    
    
    @copy_docs(ComponentBase.to_data)
    def to_data(self):
        type_ = self.type
        data = {
            'type' : type_.value
        }
        
        if type_ in COMPONENT_TYPE_ATTRIBUTE_EMOJI:
            emoji = self.emoji
            if (emoji is not None):
                data['emoji'] = create_partial_emoji_data(emoji)
        
        if type_ in COMPONENT_TYPE_ATTRIBUTE_COMPONENTS:
            components = self.components
            if (components is not None):
                data['components'] = [component.to_data() for component in components]
        
        if type_ in COMPONENT_TYPE_ATTRIBUTE_STYLE:
            style = self.style
            if (style is not None):
                data['style'] = style.value
        
        if type_ in COMPONENT_TYPE_ATTRIBUTE_URL:
            url = self.url
            if (url is not None):
                data['url'] = url
        
        if type_ in COMPONENT_TYPE_ATTRIBUTE_CUSTOM_ID:
            custom_id = self.custom_id
            if (custom_id is not None):
                data['custom_id'] = custom_id
        
        if type_ in COMPONENT_TYPE_ATTRIBUTE_LABEL:
            label = self.label
            if (label is not None):
                data['label'] = label
        
        if type_ in COMPONENT_TYPE_ATTRIBUTE_ENABLED:
            if (not self.enabled):
                data['disabled'] = True
        
        return data
    
    
    @copy_docs(ComponentBase.__repr__)
    def __repr__(self):
        repr_parts = ['<', self.__class__.__name__, ' type=']
        
        type_ = self.type
        repr_parts.append(type_.name)
        repr_parts.append(' (')
        repr_parts.append(repr(type_.value))
        repr_parts.append(')')
        
        style = self.style
        if (style is not None):
            repr_parts.append(', style=')
            repr_parts.append(style.name)
            repr_parts.append(' (')
            repr_parts.append(repr(style.value))
            repr_parts.append(')')
        
        components = self.components
        if (components is not None):
            repr_parts.append(', components=')
            repr_parts.append(repr(components))
        
        emoji = self.emoji
        if (emoji is not None):
            repr_parts.append(', emoji=')
            repr_parts.append(repr(emoji))
        
        label = self.label
        if (label is not None):
            repr_parts.append(', label=')
            repr_parts.append(reprlib.repr(label))
        
        url = self.url
        if (url is not None):
            repr_parts.append(', url=')
            repr_parts.append(url_cutter(url))
        
        custom_id = self.custom_id
        if (custom_id is not None):
            repr_parts.append(', custom_id=')
            repr_parts.append(reprlib.repr(custom_id))
        
        enabled = self.enabled
        if (not enabled):
            repr_parts.append(', enabled=')
            repr_parts.append(repr(enabled))
        
        repr_parts.append('>')
        
        return ''.join(repr_parts)
    
    @copy_docs(ComponentBase.copy)
    def copy(self):
        new = object.__new__(type(self))
        
        new.components = [component.copy() for component in self.components]
        new.custom_id = self.custom_id
        new.emoji = self.emoji
        new.style = self.style
        new.type = self.type
        new.url = self.url
        new.label = self.label
        new.enabled = self.enabled
        
        return new
    
    
    @copy_docs(ComponentBase.__eq__)
    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        
        if self.type is not other.type:
            return False
        
        if self.emoji is not other.emoji:
            return False
        
        if self.style is not other.style:
            return False
        
        if self.components != other.components:
            return False
        
        if self.custom_id != other.custom_id:
            return False
        
        if self.url != other.url:
            return False
        
        if self.label != other.label:
            return False
        
        if self.enabled != other.enabled:
            return False
        
        return True
    
    
    @copy_docs(ComponentBase.__hash__)
    def __hash__(self):
        hash_value = self.type.value
        
        emoji = self.emoji
        if (emoji is not None):
            hash_value ^= emoji.id
        
        style = self.style
        if (style is not None):
            hash_value ^= style.value
        
        components = self.components
        if (components is not None):
            hash_value ^= len(components)<<12
            for component in components:
                hash_value ^= hash(component)
        
        custom_id = self.custom_id
        if (custom_id is not None):
            hash_value ^= hash(custom_id)
        
        url = self.url
        if (url is not None):
            hash_value ^= hash(url)
        
        label = self.label
        if (label is not None):
            hash_value ^= hash(label)
        
        if self.enabled:
            hash_value ^= 1<<8
        
        return hash_value


class ComponentInteraction:
    """
    A component interaction of an ``InteractionEvent``.
    
    Attributes
    ----------
    component_type : ``ComponentType``
        The component's type.
    custom_id : `str` or `None`
        The component's custom identifier.
    """
    __slots__ = ('component_type', 'custom_id',)
    
    def __new__(cls, data, guild, cached_users):
        """
        Creates a new component interaction with the given data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            The received application command interaction data.
        guild : `None` or ``Guild``
            The respective guild.
        cached_users : `None` or `list` of ``ClientUserBase``
            Users, which might need temporary caching.
        
        Returns
        -------
        self : ``ComponentInteraction``
            The created object.
        cached_users : `None` or `list` of ``ClientUserBase``
            Users, which might need temporary caching.
        """
        self = object.__new__(cls)
        
        self.custom_id = data.get('custom_id', None)
        self.component_type = ComponentType.get(data['component_type'])
        
        return self, cached_users
    
    
    def __repr__(self):
        """Returns the component interaction's representation."""
        repr_parts = [
            '<', self.__class__.__name__,
            ' custom_id=', repr(self.custom_id),
            ', component_type=',
        ]
        component_type = self.component_type
        repr_parts.append(component_type.name)
        repr_parts.append(' (')
        repr_parts.append(repr(component_type.value))
        repr_parts.append(')')
        
        custom_id = self.custom_id
        if (custom_id is not None):
            repr_parts.append(', custom_id=')
            repr_parts.append(reprlib.repr(custom_id))
        
        repr_parts.append('>')
        
        return ''.join(repr_parts)
    
    
    def __eq__(self, other):
        """Compares the two component or component interaction."""
        other_type = type(other)
        if other_type is type(self):
            if self.component_type is not other.component_type:
                return False
            
            if self.custom_id != other.custom_id:
                return False
            
            return True
        
        if issubclass(other_type, ComponentBase):
            if self.component_type is not other.type:
                return False
            
            if self.custom_id != other.custom_id:
                return False
            
            return True
        
        
        return NotImplemented
    
    
    def __hash__(self):
        """Returns the component interaction's hash value."""
        return self.component_type.value^hash(self.custom_id)


INTERACTION_TYPE_TABLE = {
    InteractionType.ping.value: None,
    InteractionType.application_command.value: ApplicationCommandInteraction,
    InteractionType.message_component.value: ComponentInteraction,
}

COMPONENT_TYPE_TO_STYLE = {
    ComponentType.action_row: None,
    ComponentType.button: ButtonStyle,
}
