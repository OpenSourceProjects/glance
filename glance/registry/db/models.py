# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
SQLAlchemy models for glance data
"""

import sys
import datetime

from sqlalchemy.orm import relationship, backref, exc, object_mapper, validates
from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey, DateTime, Boolean, Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

from glance.common.db.sqlalchemy.session import get_session, get_engine
from glance.common import exception


BASE = declarative_base()


class ModelBase(object):
    """Base class for Nova and Glance Models"""
    __table_args__ = {'mysql_engine': 'InnoDB'}
    __table_initialized__ = False
    __protected_attributes__ = set([
        "created_at", "updated_at", "deleted_at", "deleted"])

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    deleted_at = Column(DateTime)
    deleted = Column(Boolean, default=False)

    def save(self, session=None):
        """Save this object"""
        session = session or get_session()
        session.add(self)
        session.flush()

    def delete(self, session=None):
        """Delete this object"""
        self.deleted = True
        self.deleted_at = datetime.datetime.utcnow()
        self.save(session=session)

    def update(self, values):
        """dict.update() behaviour."""
        for k, v in values.iteritems():
            self[k] = v

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        self._i = iter(object_mapper(self).columns)
        return self

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()


class Image(BASE, ModelBase):
    """Represents an image in the datastore"""
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    type = Column(String(30))
    size = Column(Integer)
    status = Column(String(30))
    is_public = Column(Boolean, default=False)
    location = Column(Text)

    @validates('type')
    def validate_type(self, key, type):
        if not type in ('machine', 'kernel', 'ramdisk', 'raw'):
            raise exception.Invalid(
                "Invalid image type '%s' for image." % type)
        return type

    @validates('status')
    def validate_status(self, key, status):
        if not status in ('active', 'queued', 'killed', 'saving'):
            raise exception.Invalid("Invalid status '%s' for image." % status)
        return status


class ImageProperty(BASE, ModelBase):
    """Represents an image properties in the datastore"""
    __tablename__ = 'image_properties'
    __table_args__ = (UniqueConstraint('image_id', 'key'), {})

    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    image = relationship(Image, backref=backref('properties'))

    key = Column(String(255), index=True)
    value = Column(Text)


def register_models():
    """Register Models and create properties"""
    engine = get_engine()
    BASE.metadata.create_all(engine)


def unregister_models():
    """Unregister Models, useful clearing out data before testing"""
    engine = get_engine()
    BASE.metadata.drop_all(engine)