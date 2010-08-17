#!/usr/bin/env python

##########################################################################
#                                                                        #
#  This program is free software; you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation; version 2 of the License.               #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#  GNU General Public License for more details.                          #
#                                                                        #
##########################################################################

from sqlalchemy import Table, MetaData, create_engine, Column, Integer, \
     String, Boolean

def get_events_table(engine=None, metadata=None):
    if engine is None:
        engine = create_engine(
            'postgresql+psycopg2://pgtharpe:tharpetharpe@tharpe/research_wiki')
    if metadata is None:
        metadata = MetaData()
        metadata.bind = engine

    events = Table('wikinetwork_wikievent', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('title', String),
                   Column('lang', String),
                   Column('desired', Boolean),
                   Column('data', String),
                   Column('talk', Boolean)
                   )
    conn = engine.connect()

    return (events, conn)