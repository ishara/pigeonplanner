# -*- coding: utf-8 -*-

# This file is part of Pigeon Planner.

# Pigeon Planner is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Pigeon Planner is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Pigeon Planner.  If not, see <http://www.gnu.org/licenses/>

import os
from typing import List, Callable, Optional, Union

from pigeonplanner.core import enums

from peewee import SqliteDatabase
from peewee import (Check, ForeignKeyField, CharField, TextField,
                    IntegerField, BooleanField, FloatField, DateField, ManyToManyField)
from playhouse.signals import (Model, pre_save, post_save, pre_delete, post_delete,
                               pre_init)


SIGNAL_MAP = {
    "pre_save": pre_save,
    "post_save": post_save,
    "pre_delete": pre_delete,
    "post_delete": post_delete,
    "pre_init": pre_init,
}

database = SqliteDatabase(None)


def all_tables() -> List["BaseModel"]:
    tables = []
    for name, obj in globals().items():
        try:
            if issubclass(obj, BaseModel) and obj != BaseModel:
                tables.append(obj)
        except TypeError:
            continue
    # TODO: any way to detect ManyToMany tables?
    tables.append(PigeonMedication)
    return tables


class DataModelMixin:
    @classmethod
    def get_data_list(cls) -> List[str]:
        column = cls.get_item_column()  # noqa
        data = (cls.select(column)  # noqa
                .order_by(column.asc())
                .dicts())
        return [item[column.name] for item in data]


class CoordinatesMixin:
    @property
    def latitude_float(self) -> Optional[float]:
        try:
            return float(self.latitude)  # noqa
        except ValueError:
            return None

    @property
    def longitude_float(self) -> Optional[float]:
        try:
            return float(self.longitude)  # noqa
        except ValueError:
            return None

    def has_valid_coordinates(self) -> bool:
        return self.latitude_float is not None and self.longitude_float is not None


class BaseModel(Model):
    defaults_fields_excludes = ["id"]

    class Meta:
        database = database

    def update_and_return(self, **kwargs) -> "BaseModel":
        cls = self.__class__
        update_query = cls.update(**kwargs).where(cls.id == self.id)
        update_query.execute()
        return cls.get(cls.id == self.id)

    @classmethod
    def get_fields_with_defaults(cls) -> dict:
        data_fields = {name: field.default for (name, field) in
                       cls._meta.fields.items() if name not in cls.defaults_fields_excludes}
        return data_fields

    # This will enable connecting signals directly on the class. Example:
    #   Pigeon.connect("post_save", on_pigeon_post_save)
    @classmethod
    def connect(cls, signal: str, handler: Callable):
        signal_func = SIGNAL_MAP[signal]
        signal_func.connect(handler, sender=cls)


# The upgrade_dummy table is very important and shouldn't be removed!
# The 1.x serie of Pigeon Planner had a schema checking function which
# updated the database to the latest schema and raised a KeyError by
# one of the helper methods which indicated that the database contained
# a table that didn't exist in the schema. The main startup script would
# catch this error and show a nice dialog that told the user the database
# was too new. The 2.x series changed all of this behaviour, but we'd still
# like to show this dialog instead of an unexpected exception dialog when
# the user tries to open this database in the 1.x series.
# From 2.x onwards the database user_version pragma is used.
class UpgradeDummy(BaseModel):
    dummy = TextField(null=True)

    class Meta:
        table_name = "upgrade_dummy"


###################
# Pigeon
###################
class Pigeon(BaseModel):
    band_number = CharField()
    band_year = CharField()
    band_country = CharField(default="")
    band_letters = CharField(default="")
    band_format = CharField(default="{empty}{empty}{number} / {year}")
    sex = IntegerField()
    visible = BooleanField(default=True)
    colour = CharField(default="")
    name = CharField(default="")
    strain = CharField(default="")
    loft = CharField(default="")
    sire = ForeignKeyField("self", null=True, backref="children_sire",
                           on_delete="SET NULL")
    dam = ForeignKeyField("self", null=True, backref="children_dam",
                          on_delete="SET NULL")
    extra1 = CharField(default="")
    extra2 = CharField(default="")
    extra3 = CharField(default="")
    extra4 = CharField(default="")
    extra5 = CharField(default="")
    extra6 = CharField(default="")

    class Meta:
        table_name = "pigeon"
        indexes = (
            (("band_number", "band_year"), False),
            (("band_country", "band_letters", "band_number", "band_year"), True),
        )

    def __repr__(self):
        return "<Pigeon %s>" % self.band

    @classmethod
    def get_for_band(cls, band_tuple: tuple) -> "Pigeon":
        country, letters, number, year = band_tuple
        return cls.get((cls.band_country == country) & (cls.band_letters == letters) &
                       (cls.band_number == number) & (cls.band_year == year))

    @property
    def band(self) -> str:
        values = {
            "country": self.band_country,
            "letters": self.band_letters,
            "number": self.band_number,
            "year": self.band_year,
            "year_short": self.band_year[2:],
            "empty": "",
        }
        return self.band_format.format(**values)  # noqa

    @property
    def band_tuple(self) -> tuple:
        return self.band_country, self.band_letters, self.band_number, self.band_year

    @property
    def sex_string(self) -> str:
        return enums.Sex.get_string(self.sex)

    def is_cock(self) -> bool:
        return self.sex == enums.Sex.cock

    def is_hen(self) -> bool:
        return self.sex == enums.Sex.hen

    def is_youngbird(self) -> bool:
        return self.sex == enums.Sex.youngbird

    def is_unknown(self) -> bool:
        return self.sex == enums.Sex.unknown

    @property
    def status(self) -> "Status":
        return self.statuses.get()

    # Used for the pigeon filter
    @property
    def status_id(self):
        return self.status.status_id

    @property
    def sire_filter(self) -> Union[tuple, str]:
        try:
            return self.sire.band_tuple
        except AttributeError:
            return ""

    @property
    def dam_filter(self) -> Union[tuple, str]:
        try:
            return self.dam.band_tuple
        except AttributeError:
            return ""

    @property
    def extra(self) -> tuple:
        return (self.extra1, self.extra2, self.extra3,
                self.extra4, self.extra5, self.extra6)

    @property
    def main_image(self) -> Optional["Image"]:
        try:
            return self.images.where(Image.main == True).get()  # noqa
        except Image.DoesNotExist:
            return None


class Status(BaseModel):
    pigeon = ForeignKeyField(Pigeon, unique=True, backref="statuses", on_delete="CASCADE")
    status_id = IntegerField(default=enums.Status.active)
    info = TextField(default="")
    date = DateField(default="")
    start = DateField(default="")
    end = DateField(default="")
    racepoint = CharField(default="")
    person = CharField(default="")
    partner = ForeignKeyField(Pigeon, null=True, on_delete="SET NULL",
                              backref="status_partner")

    defaults_fields_excludes = ["id", "pigeon", "status_id"]

    class Meta:
        table_name = "status"

    def __repr__(self):
        return "<Status %s for %s>" % (self.status_id, self.pigeon.band)

    @property
    def status_string(self) -> str:
        return enums.Status.get_string(self.status_id)


class Image(BaseModel):
    pigeon = ForeignKeyField(Pigeon, backref="images", on_delete="CASCADE")
    path = CharField()
    main = BooleanField()

    class Meta:
        table_name = "image"

    def __repr__(self):
        return "<Image %s for %s>" % (self.path, self.pigeon.band)

    @property
    def exists(self) -> bool:
        return os.path.exists(self.path)  # noqa


class Result(BaseModel):
    pigeon = ForeignKeyField(Pigeon, backref="results", on_delete="CASCADE")
    date = DateField()
    racepoint = CharField()
    place = IntegerField()
    out = IntegerField()
    category = CharField(default="")
    type = CharField(default="")
    sector = CharField(default="")
    speed = FloatField(default=0.0)
    weather = CharField(default="")
    temperature = CharField(default="")
    wind = CharField(default="")
    windspeed = CharField(default="")
    comment = TextField(default="")

    class Meta:
        table_name = "result"
        indexes = (
            (("date", "racepoint"), False),
            (("pigeon", "date", "racepoint", "place", "out", "category", "sector"), True),
        )

    def __repr__(self):
        return "<Result %s for %s>" % (self.id, self.pigeon.band)


class Breeding(BaseModel):
    sire = ForeignKeyField(Pigeon, backref="breeding_sire", on_delete="CASCADE")
    dam = ForeignKeyField(Pigeon, backref="breeding_dam", on_delete="CASCADE")
    date = DateField()
    laid1 = DateField(default="")
    hatched1 = DateField(default="")
    child1 = ForeignKeyField(Pigeon, null=True, backref="breeding_child1",
                             on_delete="SET NULL")
    success1 = BooleanField(default=False)
    laid2 = DateField(default="")
    hatched2 = DateField(default="")
    child2 = ForeignKeyField(Pigeon, null=True, backref="breeding_child2",
                             on_delete="SET NULL")
    success2 = BooleanField(default=False)
    clutch = CharField(default="")
    box = CharField(default="")
    comment = TextField(default="")

    class Meta:
        table_name = "breeding"

    def __repr__(self):
        return "<Breeding %s on %s>" % (self.id, self.date)


class Media(BaseModel):
    pigeon = ForeignKeyField(Pigeon, backref="media", on_delete="CASCADE")
    path = CharField()
    type = CharField()
    title = CharField(default="")
    description = TextField(default="")

    class Meta:
        table_name = "media"

    def __repr__(self):
        return "<Media %s (%s)>" % (self.title, self.path)


class Medication(BaseModel):
    pigeons = ManyToManyField(Pigeon, backref="medication")
    date = DateField()
    description = TextField(default="")
    doneby = CharField(default="")
    medication = CharField(default="")
    dosage = CharField(default="")
    comment = TextField(default="")
    vaccination = BooleanField(default=False)

    class Meta:
        table_name = "medication"


PigeonMedication = Medication.pigeons.get_through_model()


###################
# Data
###################
class Person(BaseModel, CoordinatesMixin):
    name = CharField()
    me = BooleanField()
    street = CharField(default="")
    zipcode = CharField(default="")
    city = CharField(default="")
    country = CharField(default="")
    phone = CharField(default="")
    email = CharField(default="")
    latitude = CharField(default="")
    longitude = CharField(default="")
    comment = TextField(default="")

    class Meta:
        table_name = "person"

    def __repr__(self):
        return "<Person %s>" % self.name


class Category(BaseModel, DataModelMixin):
    category = CharField(unique=True, constraints=[Check("category != ''")])

    class Meta:
        table_name = "category"

    @classmethod
    def get_item_column(cls):
        return cls.category


class Colour(BaseModel, DataModelMixin):
    colour = CharField(unique=True, constraints=[Check("colour != ''")])

    class Meta:
        table_name = "colour"

    @classmethod
    def get_item_column(cls):
        return cls.colour


class Loft(BaseModel, DataModelMixin):
    loft = CharField(unique=True, constraints=[Check("loft != ''")])

    class Meta:
        table_name = "loft"

    @classmethod
    def get_item_column(cls):
        return cls.loft


class Racepoint(BaseModel, DataModelMixin, CoordinatesMixin):
    racepoint = CharField(unique=True, constraints=[Check("racepoint != ''")])
    distance = CharField(default="")
    unit = IntegerField(default=0)
    xco = CharField(default="")
    yco = CharField(default="")

    class Meta:
        table_name = "racepoint"

    @classmethod
    def get_item_column(cls):
        return cls.racepoint

    # TODO: change xco/yco fields to latitude/longitude in a future schema migration
    @property
    def latitude(self):
        return self.xco

    @property
    def longitude(self):
        return self.yco


class Sector(BaseModel, DataModelMixin):
    sector = CharField(unique=True, constraints=[Check("sector != ''")])

    class Meta:
        table_name = "sector"

    @classmethod
    def get_item_column(cls):
        return cls.sector


class Strain(BaseModel, DataModelMixin):
    strain = CharField(unique=True, constraints=[Check("strain != ''")])

    class Meta:
        table_name = "strain"

    @classmethod
    def get_item_column(cls):
        return cls.strain


class Type(BaseModel, DataModelMixin):
    type = CharField(unique=True, constraints=[Check("type != ''")])

    class Meta:
        table_name = "type"

    @classmethod
    def get_item_column(cls):
        return cls.type


class Weather(BaseModel, DataModelMixin):
    weather = CharField(unique=True, constraints=[Check("weather != ''")])

    class Meta:
        table_name = "weather"

    @classmethod
    def get_item_column(cls):
        return cls.weather


class Wind(BaseModel, DataModelMixin):
    wind = CharField(unique=True, constraints=[Check("wind != ''")])

    class Meta:
        table_name = "wind"

    @classmethod
    def get_item_column(cls):
        return cls.wind
