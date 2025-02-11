__all__ = ('SolarClient', )

from random import choice
from threading import current_thread

from ...backend.utils import to_json, WeakReferer
from ...backend.headers import AUTHORIZATION, CONTENT_TYPE
from ...backend.futures import Task, WaitTillAll
from ...backend.event_loop import EventThread

from ...discord.core import KOKORO
from ...discord.voice.utils import try_get_voice_region
from ...discord.bases import maybe_snowflake_pair
from ...discord.channel import ChannelVoiceBase
from ...discord.client import Client

from .event_handler_plugin import SolarLinkEventManager
from .exceptions import SolarAuthenticationError
from .node import SolarNode
from .player import SolarPlayer
from .track import Track, GetTracksResult
from .route_planner import get_route_planner
from .player_base import SolarPlayerBase

class SolarClient:
    """
    Represents a lavalink client used to manage nodes and connections.
    
    Attributes
    ----------
    _client_reference : ``Weakreferer`` to ``Client``
        Weakreference to the extended client instance.
    _events : ``SolarLinkEventManager``
        Event plugin for solarlink specific events.
    _player_queue : `None` or `list` of ``SolarPlayerBase``
        Solar players to join back to a node.
    nodes : `set` of ``SolarNode``
        All nodes the client is connected to.
    players : `dict` of (`int`, ``SolarPlayerBase``) items
        Active players of the client by their guild's identifier as key.
    """
    __slots__ = ('_client_reference', '_events', '_player_queue', 'nodes', 'players')
    
    def __new__(cls, client):
        """
        Creates and binds a lavalink manager client.
        
        Parameters
        ----------
        client : ``Client``
            Hata client instance to extend.
        """
        if not isinstance(client, Client):
            raise TypeError(f'`client` parameter can be ``Client`` instance, got {client.__class__.__name__}.')
        
        event_plugin = SolarLinkEventManager()
        client.events.register_plugin(event_plugin)
        
        client_reference = WeakReferer(client)
        
        self = object.__new__(cls)
        self._client_reference = client_reference
        self.nodes = set()
        self.players = {}
        self._player_queue = None
        self._events = event_plugin
        return self
    
    def add_node(self, host, port, password, region, resume_key=None, reconnect_attempts=3):
        """
        Adds a node to Lavalink's node manager.
        
        The return of the method depends on the thread, from which it was called from.
        
        Parameters
        ----------
        host : `str`
            The address of the lavalink node.
        port : `int`
            The port used by the lavalink node.
        password : `str`
            The password used for authentication.
        region : `str`
            The region to assign this node to.
        resume_key : `str`, Optional
            A resume key used for resuming a session upon re-establishing a WebSocket connection to Lavalink.
            Defaults to `None`.
        reconnect_attempts : `int`, Optional
            The amount of times connection with the node will be reattempted before giving up.
            Set to `-1` for infinite. Defaults to `3`.
        
        Returns
        -------
        task : `bool`, ``Task`` or ``FutureAsyncWrapper``
            - If the method was called from the client's thread (KOKORO), then returns a ``Task``. The task will return
                `True`, if connecting was successful.
            - If the method was called from an ``EventThread``, but not from the client's, then returns a
                `FutureAsyncWrapper`. The task will return `True`, if connecting was successful.
            - If the method was called from any other thread, then waits for the connector task to finish and returns
                `True`, if it was successful.
        
        Raises
        ------
        RuntimeError
            If the ``SolarClient``'s client is already deconstructed.
        TypeError
            - If `host` is not `str` instance.
            - If `port` is not `int` instance.
            - If `password is not `str` instance.
            - If `region` is neither `None`, nor ``VoiceRegion`` instance.
            - If `resume_key` is neither `None`, nor `str` instance.
        """
        client = self._client_reference()
        if client is None:
            raise RuntimeError(f'`{self.__class__.__name__}` client is deconstructed.')
        
        node = SolarNode(
            client,
            host,
            port,
            password,
            region,
            resume_key,
            reconnect_attempts,
        )
        
        self.nodes.add(node)
        
        task = Task(node.start(), KOKORO)
        
        thread = current_thread()
        if thread is KOKORO:
            return task
        
        if isinstance(thread, EventThread):
            # `.async_wrap` wakes up KOKORO
            return task.async_wrap(thread)
        
        KOKORO.wake_up()
        return task.sync_wrap().wait()
    
    
    async def get_tracks(self, query):
        """
        Gets all tracks associated with the given query.
        
        Parameters
        ----------
        query: : `str`
            The query to perform a search for.
        
        Returns
        -------
        tracks : `None` or ``GetTracksResult``
            Decoded tracks.
        
        Raises
        ------
        RuntimeError
            - If there are no available nodes.
            - If the ``SolarClient``'s client is already deconstructed.
        SolarAuthenticationError
            Authentication failed towards the node.
        """
        available_nodes = self.available_nodes
        if not available_nodes:
            raise RuntimeError('No available nodes!')
        
        client = self._client_reference()
        if client is None:
            raise RuntimeError(f'`{self.__class__.__name__}` client is deconstructed.')
        
        node = choice(self.available_nodes)
        
        async with client.http.get(
            f'http://{node._host}:{node._port}/loadtracks',
            headers = {
                AUTHORIZATION: node._password,
            },
            params = {
                'identifier': query,
            },
        ) as response:
            if response.status == 200:
                data = await response.json()
            
            elif response.status in (401, 403):
                raise SolarAuthenticationError(node, response)
            
            else:
                data = None
        
        if data is None:
            result = None
        else:
            result = GetTracksResult(data)
        
        return result
    
    
    async def decode_track(self, track):
        """
        Decodes a base64-encoded track string into a dictionary.
        
        Parameters
        ----------
        track : `str`
            The base64-encoded track string.
        
        Returns
        -------
        track : `None` or ``Track``
            Decoded track data.
        
        Raises
        ------
        RuntimeError
            - If there are no available nodes.
            - If the ``SolarClient``'s client is already deconstructed.
        SolarAuthenticationError
            Authentication failed towards the node.
        """
        client = self._client_reference()
        if client is None:
            raise RuntimeError(f'`{self.__class__.__name__}` client is deconstructed.')
        
        available_nodes = self.available_nodes
        if not available_nodes:
            raise RuntimeError('No available nodes!')
        
        node = choice(self.available_nodes)
        
        async with client.http.get(
            f'http://{node._host}:{node._port}/decodetrack',
            headers = {
                AUTHORIZATION: node._password,
            },
            params = {
                'track': track
            },
        ) as response:
            if response.status == 200:
                track_data = await response.json()
            
            elif response.status == 401 or response.status == 403:
                raise SolarAuthenticationError(node, response)
            
            else:
                track_data = None
        
        if track_data is None:
            track = None
        else:
            track = Track(track_data)
        
        return track
    
    
    async def decode_tracks(self, tracks):
        """
        Decodes a list of base64-encoded track strings.
        
        Parameters
        ----------
        tracks : `list` of `str`
            A list of base64-encoded track strings.
        
        Returns
        -------
        tracks : `list` of ``Track``
            The decoded tracks.
        
        Raises
        ------
        RuntimeError
            - If there are no available nodes.
            - If the ``SolarClient``'s client is already deconstructed.
        SolarAuthenticationError
            Authentication failed towards the node.
        """
        client = self._client_reference()
        if client is None:
            raise RuntimeError(f'`{self.__class__.__name__}` client is deconstructed.')
        
        available_nodes = self.available_nodes
        if not available_nodes:
            raise RuntimeError('No available nodes!')
        
        node = choice(available_nodes)
        
        async with client.http.post(
            f'http://{node._host}:{node._port}/decodetracks',
            headers = {
                AUTHORIZATION: node._password,
                CONTENT_TYPE: 'application/json',
            },
            data = to_json(tracks),
        ) as response:
            if response.status == 200:
                track_datas = await response.json()
            
            elif response.status in (401, 403):
                raise SolarAuthenticationError(node, response)
            
            else:
                track_datas = None
        
        if (track_datas is None) or (not track_datas):
            tracks = []
        else:
            tracks = [Track(track_data) for track_data in track_datas]
        
        return tracks
    
    async def routeplanner_status(self, node):
        """
        Gets the routeplanner status of the target node.
        
        This method is a coroutine.
        
        Parameters
        ----------
        node : ``SolarNode``
            The node to use for the query.
        
        Returns
        -------
        route_planner : `None` or ``RoutePlannerBase`` instance
        
        Raises
        ------
        RuntimeError
            If the ``SolarClient``'s client is already deconstructed.
        """
        client = self._client_reference()
        if client is None:
            raise RuntimeError(f'`{self.__class__.__name__}` client is deconstructed.')
        
        async with client.http.get(
            f'http://{node._host}:{node._port}/routeplanner/status',
            headers = {
                AUTHORIZATION: node._password,
            },
        ) as response:
            if response.status == 200:
                route_planner_data = await response.json()
            
            elif response.status in (401, 403):
                raise SolarAuthenticationError(node, response)
            
            else:
                route_planner_data = None
        
        if route_planner_data is None:
            route_planner = None
        else:
            route_planner = get_route_planner(route_planner_data)
        
        return route_planner
        
    
    async def routeplanner_free_address(self, node, address):
        """
        Removes a single address from the addresses which are currently marked as failing.
        
        This method is a coroutine.
        
        Parameters
        ----------
        node : ``SolarNode``
            The node to use for the query.
        address : `str`
            The address to free.
        
        Returns
        -------
        success : `bool`
            Whether the address is freed up.
        
        Raises
        ------
        SolarAuthenticationError
            Authentication failed towards the node.
        RuntimeError
            If the ``SolarClient``'s client is already deconstructed.
        """
        client = self._client_reference()
        if client is None:
            raise RuntimeError(f'`{self.__class__.__name__}` client is deconstructed.')
        
        async with client.http.post(
            f'http://{node._host}:{node._port}/routeplanner/free/address',
            headers = {
                AUTHORIZATION: node._password,
                CONTENT_TYPE: 'application/json',
            },
            data = to_json(
                {'address': address}
            ),
        ) as response:
            status = response.status
            if status in (401, 403):
                raise SolarAuthenticationError(node, response)
            
            if status == 204:
                # Success
                return True
            
            if status == 500:
                # The node has no routeplanner configured.
                return False
            
            # Unexpected case.
            return False
    
    
    async def routeplanner_free_address_all(self, node):
        """
        Removes all addresses from the list which holds the addresses which are marked failing.
        
        This method is a coroutine.
        
        Parameters
        ----------
        node : ``SolarNode``
            The node to use for the query.
        
        Returns
        -------
        success : `bool`
        
        Raises
        ------
        SolarAuthenticationError
            Authentication failed towards the node.
        RuntimeError
            If the ``SolarClient``'s client is already deconstructed.
        """
        client = self._client_reference()
        if client is None:
            raise RuntimeError(f'`{self.__class__.__name__}` client is deconstructed.')
        
        async with client.http.post(
            f'http://{node._host}:{node._port}/routeplanner/free/all',
            headers = {
                AUTHORIZATION: node._password,
            },
        ) as response:
            status = response.status
            if status in (401, 403):
                raise SolarAuthenticationError(node, response)
            
            if status == 204:
                # Success
                return True
            
            if status == 500:
                # The node has no routeplanner configured
                return False
            
            # Unexpected case.
            return False
    
    
    @property
    def available_nodes(self):
        """
        Returns a list of available nodes.
        
        Returns
        -------
        available_nodes : `list` of ``SolarNode``
        """
        return [node for node in self.nodes if node.available]
    
    
    def remove_node(self, node):
        """
        Removes a node.
        
        Parameters
        ----------
        node : ``SolarNode``
            The node to remove from the list.
        """
        self.nodes.discard(node)
    
    
    def find_ideal_node(self, region=None):
        """
        Finds the least used node in the given region.
        
        Parameters
        ----------
        region : `None` or ``VoiceRegion``, Optional
            The region to find a node in. Defaults to `None`.
        
        Returns
        -------
        node : `None` or ``SolarNode``
        """
        nodes = self.available_nodes
        if not nodes:
            return None
        
        if (region is not None):
            region_nodes = [node for node in nodes if node.region is region]
            if region_nodes:
                nodes = region_nodes
        
        return min(nodes, key=node_penalty_key)
    
    
    async def _node_connected(self, node):
        """
        Called when a node is connected from Lavalink.
        
        Parameters
        ----------
        node : `SolarNode`
            The node that has just connected.
        """
        player_queue = self._player_queue
        if (player_queue is not None):
            tasks = []
            for player in player_queue:
                task = Task(player.change_node(node), KOKORO)
                tasks.append(task)
            
            self._player_queue = None
            
            await WaitTillAll(tasks, KOKORO)
    
    
    async def _node_disconnected(self, node):
        """
        Called when a node is disconnected from Lavalink.
        
        Parameters
        ----------
        node : `SolarNode`
            The node that has just connected.
        """
        players = node.players
        
        if players:
            best_node = self.find_ideal_node(node.region)
            if best_node is None:
                player_queue = self._player_queue
                if player_queue is None:
                    player_queue = list(players)
                    self._player_queue = player_queue
                else:
                    player_queue.extend(players)
            else:
                tasks = []
                for player in players:
                    task = Task(player.change_node(best_node), KOKORO)
                    tasks.append(task)
                
                await WaitTillAll(tasks, KOKORO)
    
    
    def get_player(self, guild_id):
        """
        Gets a player.
        
        Parameters
        ----------
        guild_id : `int`
            The guild's identifier where the player is.
        
        Returns
        -------
        player : `None` or ``Player``
            Returns `None` if the guild has no player.
        """
        return self.players.get(guild_id, None)
    
    
    async def join_voice(self, channel, *, cls=SolarPlayer):
        """
        Joins a solar player to the channel. If there is an already existing solar player at the respective guild,
        moves it.
        
        This method is a coroutine.
        
        Parameters
        ----------
        channel : ``ChannelVoiceBase`` or `tuple` (`int`, `int`)
            The channel to join to.
        cls : ``SolarPlayerBase`` subclass, Optional (Keyword only)
            The player's class to create.
            
            Defaults to ``SolarPlayer``.
        
        Returns
        -------
        solar_player : ``SolarPlayerBase``
        
        Raises
        ------
        TypeError
            If `channel` was not given neither as ``ChannelVoiceBase`` nor as `tuple` (`int`, `int`).
        RuntimeError
            - If there are no available nodes.
            - If the ``SolarClient``'s client is already deconstructed.
        """
        if (cls is not SolarPlayer) and (not issubclass(cls, SolarPlayerBase)):
            raise TypeError(f'`cls` can be given as `{SolarPlayerBase.__name__}` subclass, got {cls!r}.')
        
        if isinstance(channel, ChannelVoiceBase):
            guild_id = channel.guild_id
            channel_id = channel.id
        else:
            snowflake_pair = maybe_snowflake_pair(channel)
            if snowflake_pair is None:
                raise TypeError(f'`channel` can be given as `{ChannelVoiceBase.__name__}` or `tuple` (`int`, `int`)'
                    f'instance, got {channel.__class__.__name__}.')
            
            guild_id, channel_id = snowflake_pair
        
        try:
            player = self.players[guild_id]
        except KeyError:
            region = try_get_voice_region(guild_id, channel_id)
            node = self.find_ideal_node(region)
            if node is None:
                raise RuntimeError('No available nodes!')
            
            player, waiter = cls(node, guild_id, channel_id)
            self.players[guild_id] = player
            await waiter
        
        else:
            if player.channel_id != channel_id:
                client = self._client_reference()
                if client is None:
                    raise RuntimeError(f'`{self.__class__.__name__}` client is deconstructed.')
                
                gateway = client.gateway_for(guild_id)
                await gateway.change_voice_state(guild_id, channel_id)
        
        return player
    
    
    def __repr__(self):
        """Returns the solar client's representation."""
        repr_parts = ['<', self.__class__.__name__]
        
        node_count = len(self.nodes)
        if node_count:
            repr_parts.append(' node count=')
            repr_parts.append(repr(node_count))
        
        player_count = len(self.players)
        if player_count:
            repr_parts.append(' player count=')
            repr_parts.append(repr(player_count))
        
        player_queue = self._player_queue
        if (player_queue is not None):
            repr_parts.append(' queued up players=')
            repr_parts.append(len(player_queue))
        
        repr_parts.append('>')
        
        return ''.join(repr_parts)


def node_penalty_key(node):
    """
    Key sued inside of ``SolarClient.find_ideal_node`` when deciding which is the ideal node based on their penalty.
    
    Parameters
    ----------
    node : ``SolarNode``
        A respective node.
    
    Returns
    -------
    penalty : `float`
        The node's penalty.
    """
    return node.penalty
