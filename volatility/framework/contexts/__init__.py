from volatility.framework import validity, interfaces, symbols, layers, config
from volatility.framework.symbols import native
import volatility


__author__ = 'mike'

from volatility.framework.contexts import intel, physical, windows


class ContextFactory(validity.ValidityRoutines, list):
    """Class to establish and load the appropriate components of the context for a given operating system"""

    def __setitem__(self, key, value):
        self._type_check(value)
        super(ContextFactory, self).__setitem__(key, value)

    def get_config_requirements(self):
        """Returns all the possible configuration options that might be required for this particular ContextFactory"""
        # TODO: Chainmap the options from each component
        for modifier in self:
            modifier.get_config_options()

    def __call__(self):
        """Constructs a standard context based on the architecture information

        Returns a new context with all appropriate modifications (symbols, layers, etc)
        """
        context = Context(native.x86NativeTable)

        for modifier in self:
            modifier(context = context)
        return context


class Context(interfaces.context.ContextInterface):
    """Maintains the context within which to construct objects

    The context object is the main method of carrying around state that's been constructed for the purposes of
    investigating memory.  It contains a symbol_space of all the symbols that can be accessed by plugins using the
    context.  It also contains the memory made up of data and translation layers, and it contains a factory method
    for creating new objects.
    """

    def __init__(self, natives = symbols.native.x86NativeTable):
        """Initializes the context.

        This initializes the context and provides a default set of native types for the empty symbol space.

        :param natives: Defines the native types such as integers, floats, arrays and addresses.
        :type natives: interfaces.symbols.NativeTableInterface
        """
        interfaces.context.ContextInterface.__init__(self)
        self._symbol_space = symbols.SymbolSpace(natives)
        self._memory = layers.Memory()
        self._config = config.ConfigGroup(name = 'volatility')

    # ## Symbol Space Functions

    @property
    def config(self):
        """Returns the configuration object for this context"""
        return self._config

    @config.setter
    def config(self, value):
        if not isinstance(value, config.ConfigGroup):
            raise TypeError("Configuration must of type ConfigGroup")
        self._config = value

    @property
    def symbol_space(self):
        """The space of all symbols that can be accessed within this context.
        """
        return self._symbol_space

    @property
    def memory(self):
        """A Memory object, allowing access to all data and translation layers currently available within the context"""
        return self._memory

    # ## Address Space Functions

    def add_translation_layer(self, layer):
        """Adds a named translation layer to the context

        :param layer: The layer to be added to the memory
        :type layer: volatility.framework.interfaces.layers.DataLayerInterface
        :raises volatility.framework.exceptions.LayerException: if the layer is already present, or has
        unmet dependencies
        """
        self._memory.add_layer(layer)

    # ## Object Factory Functions

    def object(self, symbol, layer_name, offset, **arguments):
        """Object factory, takes a context, symbol, offset and optional layername

        Looks up the layername in the context, finds the object template based on the symbol,
        and constructs an object using the object template on the layer at the offset.

        :return: A fully constructed object
        :rtype: :py:class:`volatility.framework.interfaces.objects.ObjectInterface`
        """
        object_template = self._symbol_space.get_structure(symbol)
        object_template.update_vol(**arguments)
        return object_template(context = self,
                               object_info = interfaces.objects.ObjectInformation(layer_name = layer_name,
                                                                                  offset = offset))