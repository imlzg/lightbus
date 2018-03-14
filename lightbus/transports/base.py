from typing import Sequence, Tuple, List, Generator, Dict, NamedTuple, Optional, TypeVar, Type, Callable

from lightbus.api import Api
from lightbus.exceptions import NothingToListenFor
from lightbus.message import RpcMessage, EventMessage, ResultMessage

T = TypeVar('T')


class RpcTransport(object):
    """Implement the sending and receiving of RPC calls"""

    async def call_rpc(self, rpc_message: RpcMessage, options: dict):
        """Publish a call to a remote procedure"""
        RpcTransport.from_config()
        raise NotImplementedError()

    async def consume_rpcs(self, apis: Sequence[Api]) -> Sequence[RpcMessage]:
        """Consume RPC calls for the given API"""
        raise NotImplementedError()

    @classmethod
    def get_config_structure(self) -> Optional[NamedTuple]:
        return None

    @classmethod
    def from_config(cls: Type[T]) -> T:
        return cls()


class ResultTransport(object):
    """Implement the send & receiving of results

    """

    def get_return_path(self, rpc_message: RpcMessage) -> str:
        raise NotImplementedError()

    async def send_result(self, rpc_message: RpcMessage, result_message: ResultMessage, return_path: str):
        """Send a result back to the caller

        Args:
            rpc_message (): The original message received from the client
            result_message (): The result message to be sent back to the client
            return_path (str): The string indicating where to send the result.
                As generated by :ref:`get_return_path()`.
        """
        raise NotImplementedError()

    async def receive_result(self, rpc_message: RpcMessage, return_path: str, options: dict) -> ResultMessage:
        """Receive the result for the given message

        Args:
            rpc_message (): The original message sent to the server
            return_path (str): The string indicated where to receive the result.
                As generated by :ref:`get_return_path()`.
            options (dict): Dictionary of options specific to this particular backend
        """
        raise NotImplementedError()

    @classmethod
    def get_config_structure(self) -> Optional[NamedTuple]:
        return None

    @classmethod
    def from_config(cls, config: NamedTuple) -> 'ResultTransport':
        return cls(**config._asdict())


class EventTransport(object):
    """ Implement the sending/consumption of events over a given transport.
    """

    async def send_event(self, event_message: EventMessage, options: dict):
        """Publish an event"""
        raise NotImplementedError()

    def consume(self, listen_for: List[Tuple[str, str]], context: dict, **kwargs):
        """Consume messages for the given APIs

        Examples:

            Consuming events::

                listen_for = [
                    ('mycompany.auth', 'user_created'),
                    ('mycompany.auth', 'user_updated'),
                ]
                async with event_transport.consume(listen_for) as event_message:
                    print(event_message)

        """
        if not listen_for:
            raise NothingToListenFor(
                'EventTransport.consume() was called without providing anything '
                'to listen for in the "listen_for" argument.'
            )
        return self.fetch(listen_for, context, **kwargs)

    async def fetch(self, listen_for: List[Tuple[str, str]], context:dict, **kwargs) -> Generator[EventMessage, None, None]:
        """Consume RPC messages for the given events

        Events the bus is not listening for may be returned, they
        will simply be ignored.
        """
        raise NotImplementedError()

    async def consumption_complete(self, event_message: EventMessage, context: dict):
        pass

    @classmethod
    def get_config_structure(self) -> Optional[NamedTuple]:
        return None

    @classmethod
    def from_config(cls, config: NamedTuple) -> 'EventMessage':
        return cls(**config._asdict())


class SchemaTransport(object):
    """ Implement sharing of lightbus API schemas
    """

    async def store(self, api_name: str, schema: Dict, ttl_seconds: int):
        """Store a schema for the given API"""
        raise NotImplementedError()

    async def ping(self, api_name: str, schema: Dict, ttl_seconds: int):
        """Keep alive a schema already stored via store()

        The defaults to simply calling store() on the assumption that this
        will cause the ttl to be updated. Backends may choose to
        customise this logic.
        """
        await self.store(api_name, schema, ttl_seconds)

    async def load(self) -> Dict[str, Dict]:
        """Load the schema for all APIs

        Should return a mapping of API names to schemas
        """
        raise NotImplementedError()

    @classmethod
    def get_config_structure(self) -> Optional[NamedTuple]:
        return None

    @classmethod
    def from_config(cls, config: NamedTuple) -> 'SchemaTransport':
        return cls(**config._asdict())
