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
     String, Boolean, Sequence, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def get_engine():
    """
    returns the engine used by this project
    """
    return create_engine(
        'postgresql+psycopg2://pgtharpe:tharpetharpe@tharpe/research_wiki'
    )

def get_events_table(engine=None, metadata=None):
    if engine is None:
        engine = get_engine()
    if metadata is None:
        metadata = MetaData()
        metadata.bind = engine

    events = Table('wikinetwork_wikievent', metadata,
                   Column('id', Integer,
                          Sequence('wikinetwork_wikievent_id_seq'),
                          primary_key=True),
                   Column('title', String),
                   Column('lang', String),
                   Column('desired', Boolean),
                   Column('data', String),
                   Column('talk', Boolean)
                   )
    conn = engine.connect()

    return (events, conn)

class UserContributions(Base):
    __tablename__ = 'wikinetwork_usercontribution'

    id = Column(Integer, Sequence('wikinetwork_usercontribution_id_seq'),
                primary_key=True)
    username = Column(String)
    lang = Column(String)
    normal_edits = Column(Integer)
    namespace_edits = Column(String)
    first_edit = Column(DateTime)
    last_edit = Column(DateTime)
    comments_count = Column(Integer)
    comments_avg = Column(Float)
    minor = Column(Integer)
    welcome = Column(Integer)
    npov = Column(Integer)
    please = Column(Integer)
    thanks = Column(Integer)
    revert = Column(Integer)

def get_contributions_table(engine=None):
    if engine is None:
        engine = get_engine()
    Base.metadata.bind = engine

    table = UserContributions.__table__
    Base.metadata.create_all()
    conn = engine.connect()

    return (table, conn)