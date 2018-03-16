# -*- coding:utf-8 -*-
from webserver import db


class Location(db.Model):
    __tablename__ = 'locations'
    pid = db.Column(db.VARCHAR(255),primary_key=True)
    uname = db.Column(db.String)
    location = db.Column(db.Text(255))
    def __repr__(self):
        return '<Location %r>' % (self.pid)