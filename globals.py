from models import VCConnection, Election, Server, WSESession
from discord import Guild
import threading

servers: dict[Guild, Server] = {}
""" Contains active server connections """

vc_connections: dict[Guild, VCConnection] = {}
""" Contains active voice chat connections """

elections: dict[Guild, Election] = {}
""" Contains active elections """

live_wse_sessions: dict[Guild, WSESession] = {}
"""Contains servers with active WSE sessions """

start_mutex: threading.Semaphore = threading.Semaphore(0)
""" Mutex used to synchronize GW on_ready and shell start """
