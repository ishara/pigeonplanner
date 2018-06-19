
from pigeonplanner.core import enums

from peewee import SqliteDatabase
from peewee import (Check, ForeignKeyField, CharField, TextField,
                    IntegerField, BooleanField, FloatField, DateField)
from playhouse.signals import (Model, pre_save, post_save, pre_delete, post_delete,
                               pre_init, post_init)
from playhouse.fields import ManyToManyField


SIGNAL_MAP = {
    "pre_save": pre_save,
    "post_save": post_save,
    "pre_delete": pre_delete,
    "post_delete": post_delete,
    "pre_init": pre_init,
    "post_init": post_init
}

database = SqliteDatabase(None)


def set_database_path(path):
    database.init(path)
    return database


def all_tables():
    tables = []
    for name, obj in globals().items():
        try:
            if issubclass(obj, BaseModel):
                tables.append(obj)
        except TypeError:
            continue
    # TODO: any way to detect ManyToMany tables?
    tables.append(PigeonMedication)
    return tables


class DataModelMixin(object):
    @classmethod
    def get_data_list(cls):
        column = cls.get_item_column()
        data = (cls.select(column)
                .order_by(column.asc())
                .dicts())
        return [item[column.name] for item in data]


class BaseModel(Model):
    defaults_fields_excludes = ["id"]

    class Meta:
        database = database

    def update_and_return(self, **kwargs):
        cls = self.__class__
        update_query = cls.update(**kwargs).where(cls.id == self.id)
        update_query.execute()
        return cls.get(cls.id == self.id)

    @classmethod
    def get_fields_with_defaults(cls):
        data_fields = {name: field.default for (name, field) in
                       cls._meta.fields.items() if name not in cls.defaults_fields_excludes}
        return data_fields

    # This will enable connecting signals directly on the class. Example:
    #   Pigeon.connect("post_save", on_pigeon_post_save)
    @classmethod
    def connect(cls, signal, handler):
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
        db_table = "upgrade_dummy"


###################
# Pigeon
###################
class Pigeon(BaseModel):
    band = CharField()
    year = CharField()
    sex = IntegerField()
    visible = BooleanField(default=True)
    colour = CharField(default="")
    name = CharField(default="")
    strain = CharField(default="")
    loft = CharField(default="")
    sire = ForeignKeyField("self", null=True, related_name="children_sire",
                           on_delete="SET NULL")
    dam = ForeignKeyField("self", null=True, related_name="children_dam",
                          on_delete="SET NULL")
    extra1 = CharField(default="")
    extra2 = CharField(default="")
    extra3 = CharField(default="")
    extra4 = CharField(default="")
    extra5 = CharField(default="")
    extra6 = CharField(default="")

    class Meta:
        db_table = "Pigeons"
        indexes = (
            (("band", "year"), True),
        )

    def __repr__(self):
        return "<Pigeon %s/%s>" % (self.band, self.year)

    @classmethod
    def get_for_band(cls, band_tuple):
        band, year = band_tuple
        return cls.get((cls.band == band) & (cls.year == year))

    def get_band_string(self, short=False):
        year = self.year if not short else self.year[2:]
        return "%s / %s" % (self.band, year)

    @property
    def band_string(self):
        return self.get_band_string()

    @property
    def sex_string(self):
        return enums.Sex.get_string(self.sex)

    def is_cock(self):
        return self.sex == enums.Sex.cock

    def is_hen(self):
        return self.sex == enums.Sex.hen

    def is_youngbird(self):
        return self.sex == enums.Sex.youngbird

    def is_unknown(self):
        return self.sex == enums.Sex.unknown

    @property
    def status(self):
        return self.statuses.get()

    # Used for the pigeon filter
    @property
    def status_id(self):
        return self.status.status_id

    @property
    def sire_filter(self):
        try:
            return self.sire.band, self.sire.year
        except AttributeError:
            return ""

    @property
    def dam_filter(self):
        try:
            return self.dam.band, self.dam.year
        except AttributeError:
            return ""

    @property
    def extra(self):
        return (self.extra1, self.extra2, self.extra3,
                self.extra4, self.extra5, self.extra6)

    @property
    def main_image(self):
        try:
            return self.images.where(Image.main == True).get()
        except Image.DoesNotExist:
            return None


class Status(BaseModel):
    pigeon = ForeignKeyField(Pigeon, unique=True, related_name="statuses", on_delete="CASCADE")
    status_id = IntegerField(default=enums.Status.active)
    info = TextField(default="")
    date = DateField(default="")
    start = DateField(default="")
    end = DateField(default="")
    racepoint = CharField(default="")
    person = CharField(default="")
    partner = ForeignKeyField(Pigeon, null=True, on_delete="SET NULL",
                              related_name="status_partner")

    defaults_fields_excludes = ["id", "pigeon", "status_id"]

    class Meta:
        db_table = "Statuses"

    def __repr__(self):
        return "<Status %s for %s>" % (self.status_id, self.pigeon.band_string)

    @property
    def status_string(self):
        return enums.Status.get_string(self.status_id)


class Image(BaseModel):
    pigeon = ForeignKeyField(Pigeon, related_name="images", on_delete="CASCADE")
    path = CharField()
    main = BooleanField()

    class Meta:
        db_table = "Images"

    def __repr__(self):
        return "<Image %s for %s>" % (self.path, self.pigeon.band_string)


class Result(BaseModel):
    pigeon = ForeignKeyField(Pigeon, related_name="results", on_delete="CASCADE")
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
        db_table = "Results"
        indexes = (
            (("date", "racepoint"), False),
            (("pigeon", "date", "racepoint", "place", "out", "category", "sector"), True),
        )

    def __repr__(self):
        return "<Result %s for %s>" % (self.id, self.pigeon.band_string)


class Breeding(BaseModel):
    sire = ForeignKeyField(Pigeon, related_name="breeding_sire", on_delete="CASCADE")
    dam = ForeignKeyField(Pigeon, related_name="breeding_dam", on_delete="CASCADE")
    date = DateField()
    laid1 = DateField(default="")
    hatched1 = DateField(default="")
    child1 = ForeignKeyField(Pigeon, null=True, related_name="breeding_child1",
                             on_delete="SET NULL")
    success1 = BooleanField(default=False)
    laid2 = DateField(default="")
    hatched2 = DateField(default="")
    child2 = ForeignKeyField(Pigeon, null=True, related_name="breeding_child2",
                             on_delete="SET NULL")
    success2 = BooleanField(default=False)
    clutch = CharField(default="")
    box = CharField(default="")
    comment = TextField(default="")

    class Meta:
        db_table = "Breeding"

    def __repr__(self):
        return "<Breeding %s on %s>" % (self.id, self.date)


class Media(BaseModel):
    pigeon = ForeignKeyField(Pigeon, related_name="media", on_delete="CASCADE")
    path = CharField()
    type = CharField()
    title = CharField(default="")
    description = TextField(default="")

    class Meta:
        db_table = "Media"

    def __repr__(self):
        return "<Media %s (%s)>" % (self.title, self.path)


class Medication(BaseModel):
    pigeons = ManyToManyField(Pigeon, related_name="medication")
    date = DateField()
    description = TextField(default="")
    doneby = CharField(default="")
    medication = CharField(default="")
    dosage = CharField(default="")
    comment = TextField(default="")
    vaccination = BooleanField(default=False)

    class Meta:
        db_table = "Medication"


PigeonMedication = Medication.pigeons.get_through_model()


###################
# Data
###################
class Person(BaseModel):
    name = CharField()
    me = BooleanField()
    street = CharField(default="")
    code = CharField(default="")
    city = CharField(default="")
    country = CharField(default="")
    phone = CharField(default="")
    email = CharField(default="")
    latitude = CharField(default="")
    longitude = CharField(default="")
    comment = TextField(default="")

    class Meta:
        db_table = "People"

    def __repr__(self):
        return "<Person %s>" % self.name


class Category(BaseModel, DataModelMixin):
    category = CharField(unique=True, constraints=[Check("category != ''")])

    class Meta:
        db_table = "Categories"

    @classmethod
    def get_item_column(cls):
        return cls.category


class Colour(BaseModel, DataModelMixin):
    colour = CharField(unique=True, constraints=[Check("colour != ''")])

    class Meta:
        db_table = "Colours"

    @classmethod
    def get_item_column(cls):
        return cls.colour


class Loft(BaseModel, DataModelMixin):
    loft = CharField(unique=True, constraints=[Check("loft != ''")])

    class Meta:
        db_table = "Lofts"

    @classmethod
    def get_item_column(cls):
        return cls.loft


class Racepoint(BaseModel, DataModelMixin):
    racepoint = CharField(unique=True, constraints=[Check("racepoint != ''")])
    distance = CharField(default="")
    unit = IntegerField(default=0)
    xco = CharField(default="")
    yco = CharField(default="")

    class Meta:
        db_table = "Racepoints"

    @classmethod
    def get_item_column(cls):
        return cls.racepoint


class Sector(BaseModel, DataModelMixin):
    sector = CharField(unique=True, constraints=[Check("sector != ''")])

    class Meta:
        db_table = "Sectors"

    @classmethod
    def get_item_column(cls):
        return cls.sector


class Strain(BaseModel, DataModelMixin):
    strain = CharField(unique=True, constraints=[Check("strain != ''")])

    class Meta:
        db_table = "Strains"

    @classmethod
    def get_item_column(cls):
        return cls.strain


class Type(BaseModel, DataModelMixin):
    type = CharField(unique=True, constraints=[Check("type != ''")])

    class Meta:
        db_table = "Types"

    @classmethod
    def get_item_column(cls):
        return cls.type


class Weather(BaseModel, DataModelMixin):
    weather = CharField(unique=True, constraints=[Check("weather != ''")])

    class Meta:
        db_table = "Weather"

    @classmethod
    def get_item_column(cls):
        return cls.weather


class Wind(BaseModel, DataModelMixin):
    wind = CharField(unique=True, constraints=[Check("wind != ''")])

    class Meta:
        db_table = "Wind"

    @classmethod
    def get_item_column(cls):
        return cls.wind
