import asyncio
import logging
import traceback
from argparse import ArgumentParser, _ArgumentGroup, Namespace
from typing import Dict, Type, NamedTuple, Optional, TypeVar, Callable

import pkg_resources
from collections import OrderedDict

import lightbus
from lightbus.exceptions import PluginsNotLoaded, PluginHookNotFound, InvalidPlugins, LightbusShutdownInProgress
from lightbus.message import RpcMessage, EventMessage, ResultMessage
from lightbus.utilities.importing import load_entrypoint_classes

_plugins = None
_hooks_names = []
ENTRYPOINT_NAME = 'lightbus_plugins'


logger = logging.getLogger(__name__)


# TODO: Document plugins in docs (and reference those docs here)
class LightbusPlugin(object):
    priority = 1000

    def get_config_structure(self) -> Optional[NamedTuple]:
        return None

    @classmethod
    def from_config(cls, config: NamedTuple) -> 'LightbusPlugin':
        return cls(**config._asdict())

    def __str__(self):
        return '{}.{}'.format(self.__class__.__module__, self.__class__.__name__)

    async def before_parse_args(self, *, parser: ArgumentParser, subparsers: _ArgumentGroup):
        pass

    async def after_parse_args(self, args: Namespace):
        pass

    async def before_server_start(self, *, bus_client: 'lightbus.bus.BusClient'):
        pass

    async def after_server_stopped(self, *, bus_client: 'lightbus.bus.BusClient'):
        pass

    async def before_rpc_call(self, *, rpc_message: RpcMessage, bus_client: 'lightbus.bus.BusClient'):
        pass

    async def after_rpc_call(self, *, rpc_message: RpcMessage, result_message: ResultMessage, bus_client: 'lightbus.bus.BusClient'):
        pass

    async def before_rpc_execution(self, *, rpc_message: RpcMessage, bus_client: 'lightbus.bus.BusClient'):
        pass

    async def after_rpc_execution(self, *, rpc_message: RpcMessage, result_message: ResultMessage, bus_client: 'lightbus.bus.BusClient'):
        pass

    async def before_event_sent(self, *, event_message: EventMessage, bus_client: 'lightbus.bus.BusClient'):
        pass

    async def after_event_sent(self, *, event_message: EventMessage, bus_client: 'lightbus.bus.BusClient'):
        pass

    async def before_event_execution(self, *, event_message: EventMessage, bus_client: 'lightbus.bus.BusClient'):
        pass

    async def after_event_execution(self, *, event_message: EventMessage, bus_client: 'lightbus.bus.BusClient'):
        pass


def autoload_plugins(force=False):
    global _plugins, _hooks_names
    load_hook_names()

    if force:
        remove_all_plugins()
    if _plugins:
        return _plugins

    found_plugins = load_entrypoint_classes(ENTRYPOINT_NAME)
    found_plugins = sorted(found_plugins, key=lambda v: v[-1].priority)

    _plugins = OrderedDict()
    for module_name, name, plugin in found_plugins:
        if name in _plugins:
            pass
        _plugins[name] = plugin()

    return _plugins


def manually_set_plugins(plugins: Dict[str, LightbusPlugin]):
    """Manually set the plugins in the global plugin registry"""
    global _plugins
    if not isinstance(plugins, dict):
        raise InvalidPlugins(
            "You have attempted to specify your desired plugins as a {} ({}). This is not supported. "
            "Plugins must be specified as a dictionary, where the key is the plugin name.".format(
                type(plugins).__name__, plugins
            )
        )

    load_hook_names()
    _plugins = plugins


def load_hook_names():
    """Load a list of valid hook names"""
    global _hooks_names
    _hooks_names = [k for k in LightbusPlugin.__dict__ if not k.startswith('_')]


def remove_all_plugins():
    """Remove all plugins. Useful for testing"""
    global _plugins
    _plugins = OrderedDict()


def get_plugins() -> Dict[str, LightbusPlugin]:
    """Get all plugins as an ordered dictionary"""
    global _plugins
    return _plugins


def is_plugin_loaded(plugin_class: Type[LightbusPlugin]):
    global _plugins
    if not _plugins:
        return False
    return plugin_class in [type(p) for p in _plugins.values()]


async def plugin_hook(name, **kwargs):
    global _plugins
    if _plugins is None:
        raise PluginsNotLoaded("You must call load_plugins() before calling plugin_hook('{}').".format(name))
    if name not in _hooks_names:
        raise PluginHookNotFound("Plugin hook '{}' could not be found. Must be one of: {}".format(
            name,
            ', '.join(_hooks_names)
        ))

    return_values = []
    for plugin in _plugins.values():
        handler = getattr(plugin, name, None)
        if handler:
            try:
                return_values.append(
                    await handler(**kwargs)
                )
            except asyncio.CancelledError:
                raise
            except LightbusShutdownInProgress as e:
                logger.info('Shutdown in progress: {}'.format(e))
            except Exception as e:
                logger.error('Exception while executing plugin hook {}.{}.{}'.format(
                    plugin.__module__,
                    plugin.__class__.__name__,
                    name
                ))
                logger.exception(e)
                traceback.print_exc()

    return return_values
