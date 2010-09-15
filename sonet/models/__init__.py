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

def get_engine(dbname=None):
    """
    Returns the SQLAlchemy engine used by this project retrieving database
    information from the Django project settings.

    With dbname you can force to use a database different from the django one.
    """
    from django_wikinetwork.settings import DATABASE_ENGINE, DATABASE_HOST, \
         DATABASE_NAME, DATABASE_PASSWORD, DATABASE_PORT, DATABASE_USER

    ## maps django database engine into SQLAlchemy drivers
    driver_mapping = {
        'postgresql_psycopg2': 'postgresql+psycopg2',
        'postgresql': 'postgresql'
    }
    try:
        driver = driver_mapping[DATABASE_ENGINE]
    except KeyError:
        raise Exception, 'Database driver not recognized: %s' % (
            DATABASE_ENGINE,)

    if dbname is None:
        dbname = DATABASE_NAME

    s_engine = '%(driver)s://%(username)s:%(password)s@%(host)s/%(dbname)s' % {
        'driver': driver,
        'host': DATABASE_HOST,
        'dbname': dbname,
        'username': DATABASE_USER,
        'password': DATABASE_PASSWORD
    }

    return create_engine(
        s_engine
    )

def get_events_table(engine=None, metadata=None):
    if engine is None:
        engine = get_engine()
    if metadata is None:
        metadata = MetaData()
        metadata.bind = engine

    events = Table('wikinetwork_wikievent', metadata, autoload=True)
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
