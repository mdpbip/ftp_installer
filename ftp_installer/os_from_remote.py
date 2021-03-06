#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import virtual_map

import os_from_virtual_map

import bip

import functools

import ftplib

import ftputil

import os

import os.path

import pprint

from colorama import Fore

import sys

import socket

LOGIN			= '%s_LOGIN'		% __name__
SERVER      		= '%s_SERVER'		% __name__
PASSWORD		= '%s_PASSWORD' 	% __name__
ROOT			= '%s_ROOT'     	% __name__
OS_REMOTE_PARAMS 	= '%s_OS_REMOTE_PARAMS' % __name__

def has_os_from_remote_params( fct ):

    @functools.wraps( fct )
    def wrapped( *args, **kwargs ):

        assert( 
            kwargs.has_key( OS_REMOTE_PARAMS ) 
        ) , u'kwargs ne contient pas %s %s' 	% ( OS_REMOTE_PARAMS, kwargs )

        assert( 
            kwargs[ OS_REMOTE_PARAMS ].has_key( LOGIN ) 
        ) , u'kwargs[ %s ] ne contient pas %s %s' 	% ( OS_REMOTE_PARAMS, LOGIN, kwargs[ OS_REMOTE_PARAMS ] )

        assert( 
            kwargs[ OS_REMOTE_PARAMS ].has_key( SERVER )
        ) , u'kwargs[ %s ] ne contient pas %s %s'	% ( OS_REMOTE_PARAMS, SERVER, kwargs[ OS_REMOTE_PARAMS ] )

        assert( 
            kwargs[ OS_REMOTE_PARAMS ].has_key( PASSWORD ) 
        ) , u'kwargs[ %s] ne contient pas %s %s' 	%( OS_REMOTE_PARAMS, PASSWORD, kwargs )

        assert( 
            kwargs[ OS_REMOTE_PARAMS ].has_key( ROOT ) 
        ) , u'kwargs[ %s ] ne contient pas %s %s' 	%( OS_REMOTE_PARAMS, ROOT, kwargs )

        return fct( *args, **kwargs )

    return wrapped

# cast_unicode_to_ascii
# supprimé lors du passage de
# pyftpdlib 0.7.0 à pyftpdlib 1.4.0
# en effet, ftpuil et pyftpdlib
# son a présent syncrho sur l'usage de
# l'unicode pour les chaines de caractères
# Le module simple json n'est donc plus utile

class OsRemoteFTPSession( ftplib.FTP ):
    def __init__( self, host, userid, password ):
        """Act like ftplib.FTP's constructor but connect to another port."""
        ftplib.FTP.__init__( self )
        self.connect( host )
        self.login( userid, password )
        self.set_pasv( True )

__d_ftp_clients = {}

@bip.bip
@has_os_from_remote_params
def remote_call( *args, **kwargs ):

        assert( kwargs.has_key( 'm' ) ), u'm n\' a pas ete transmis. Impossible de continuer'
        assert( kwargs.has_key( 'fct' ) ), u'fct n\' a pas ete transmis. Impossible de continuer'

        ftp_params = (
            kwargs[ OS_REMOTE_PARAMS ][ SERVER ],
            kwargs[ OS_REMOTE_PARAMS ][ LOGIN ],
            kwargs[ OS_REMOTE_PARAMS ][ PASSWORD ],
        )

        client_key = ( 
            ftp_params[ 0 ],
            ftp_params[ 1 ],
            ftp_params[ 2 ],
        )

        kwargs_for_remote = kwargs.copy()
        del( kwargs_for_remote[ 'm' ] )
        del( kwargs_for_remote[ 'fct' ] )
        del( kwargs_for_remote[ OS_REMOTE_PARAMS ] )
        del( kwargs_for_remote[ os_from_virtual_map.PATH_PARAMS ] )

        # Recreation du client si la connexion est closed
        if not __d_ftp_clients.has_key( client_key ):
            __d_ftp_clients[ client_key ] = ftputil.FTPHost( *ftp_params, session_factory = OsRemoteFTPSession )

        if __d_ftp_clients[ client_key ].closed:
            __d_ftp_clients[ client_key ] = ftputil.FTPHost( *ftp_params, session_factory = OsRemoteFTPSession )

        try:

            if kwargs[ 'm' ] == os:
        
                return getattr(
                    __d_ftp_clients[ client_key ],
                    kwargs[ 'fct' ].__name__
                )( *args, **kwargs_for_remote )

            elif kwargs[ 'm' ] == os.path:

                return getattr(
                    __d_ftp_clients[ client_key ].path,
                    kwargs[ 'fct' ].__name__
                )( *args, **kwargs_for_remote )

        except ( ftputil.error.PermanentError, ftputil.error.FTPIOError ), pe:
            # On ne filtre pas ces exceptions
            # elles ne remontent pas à cause d'un
            # problème d'accès au serveur FTP
            raise pe

        except ( ftputil.error.TemporaryError, ftputil.error.FTPOSError, socket.error ), te:
            # Relancement de la commande
            # Lors d'une premiere exception
            # Ceci peut-etre du a un inactivite de
            # 10 minutes 
            # Si une exception a lieu de nouveau
            # Elle est transmise  
            try:
                __d_ftp_clients[ client_key ] = ftputil.FTPHost( *ftp_params, session_factory = OsRemoteFTPSession )

                if kwargs[ 'm' ] == os:

                    return getattr(
                        __d_ftp_clients[ client_key ],
                        kwargs[ 'fct' ].__name__
                    )( *args, **kwargs_for_remote )

                elif kwargs[ 'm' ] == os.path:

                    return getattr(
                        __d_ftp_clients[ client_key ].path,
                        kwargs[ 'fct' ].__name__
                    )( *args, **kwargs_for_remote )

            except Exception, e:
                print >> sys.stderr, Fore.RED, e.__class__, pprint.pformat( e ), pprint.pformat( args ), pprint.pformat( kwargs ), Fore.RESET
                raise te

        except Exception, undefined_e:
            # Erreurs non gérées spécifiquement
            # potentiellement peut donc lieu à un filtrage de l'exception
            print >> "Exception non cacthée dans les blocs précédents²", sys.stderr, Fore.RED, undefined_e.__class__, pprint.pformat( undefined_e ), pprint.pformat( args ), pprint.pformat( kwargs ), Fore.RESET
            raise
