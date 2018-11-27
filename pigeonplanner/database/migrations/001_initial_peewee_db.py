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


import time
import sqlite3
import logging
from datetime import datetime
from collections import defaultdict

from peewee import SQL
from peewee import SqliteDatabase
from peewee import IntegrityError
from peewee import (Check, ForeignKeyField, CharField, TextField,
                    IntegerField, BooleanField, FloatField, DateField, ManyToManyField)
from playhouse.signals import Model
from playhouse.migrate import migrate, SqliteMigrator

from pigeonplanner.core import enums


logger = logging.getLogger(__name__)

database_version = 3


def do_migration(db):
    db.close()
    database.init(db.database)

    start_time = time.time()

    migrator = SqliteMigrator(database)
    database.connection().row_factory = sqlite3.Row

    status_tables = ["Dead", "Sold", "Lost", "Breeder", "Onloan", "Widow"]
    old_tables = ["Pigeons", "Results", "Breeding", "Media", "Medication", "Addresses", "Categories",
                  "Colours", "Lofts", "Racepoints", "Sectors", "Strains", "Types", "Weather", "Wind"]

    logger.info("Renaming tables")
    migrators = [migrator.rename_table(table_name, table_name + "_orig") for table_name in old_tables]
    migrate(*migrators)

    logger.info("Recreating tables")
    database.create_tables(all_tables())

    with database.atomic():
        logger.info("Migrating pigeons")
        _migrate_pigeons()

        logger.info("Migrating pigeon data")
        for pigeon in Pigeon.select():
            old_pindex = pigeon.band_number + pigeon.band_year

            _migrate_parents(pigeon)
            _migrate_status(pigeon, old_pindex)
            _migrate_images(pigeon, old_pindex)
            _migrate_results(pigeon, old_pindex)
            _migrate_media(pigeon, old_pindex)

        _migrate_breeding()
        _migrate_medication()

        logger.info("Migrating data")
        _migrate_data_tables()

        logger.info("Deleting old tables")
        for table_name in status_tables:
            database.execute_sql("DROP TABLE %s" % table_name)
        for table_name in old_tables:
            database.execute_sql("DROP TABLE %s_orig" % table_name)

    database.close()
    db.connect()

    end_time = time.time()
    logger.info("Migration done in %.2f seconds!", (end_time - start_time))


def _to_date(date_str):
    if date_str == "":
        return date_str
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _split_pindex(pindex):
    band = pindex[:-4]
    year = pindex[-4:]
    return band, year


def _pigeon_for_pindex(pindex):
    band, year = _split_pindex(pindex)
    try:
        pigeon = Pigeon.get((Pigeon.band_number == band) & (Pigeon.band_year == year))
    except Pigeon.DoesNotExist:
        pigeon = None
    return pigeon


def _insert_pigeon(band_number, band_year, sex, visible):
    pigeon_id = Pigeon.insert(
        band_number=band_number,
        band_year=band_year,
        sex=sex,
        visible=visible
    ).execute()
    Status.insert(pigeon=pigeon_id).execute()
    return pigeon_id


def _migrate_pigeons():
    cursor = database.execute_sql("SELECT * FROM Pigeons_orig;")
    for row in cursor.fetchall():
        data = {
            "band_number": row["band"],
            "band_year": row["year"],
            "sex": int(row["sex"]),
            "visible": bool(row["show"]),
            "colour": row["colour"],
            "name": row["name"],
            "strain": row["strain"],
            "loft": row["loft"],
            "extra1": row["extra1"],
            "extra2": row["extra2"],
            "extra3": row["extra3"],
            "extra4": row["extra4"],
            "extra5": row["extra5"],
            "extra6": row["extra6"],
        }
        Pigeon.insert(**data).execute()


def _migrate_parents(pigeon):
    sire_row = database.execute_sql("SELECT sire, yearsire FROM Pigeons_orig WHERE sire != '' AND band=? AND year=?",
                                    (pigeon.band_number, pigeon.band_year)).fetchone()
    if sire_row is not None:
        try:
            sire = Pigeon.get((Pigeon.band_number == sire_row["sire"]) &
                              (Pigeon.band_year == sire_row["yearsire"]))
        except Pigeon.DoesNotExist:
            _insert_pigeon(sire_row["sire"], sire_row["yearsire"], enums.Sex.cock, False)
        else:
            pigeon.sire = sire
            pigeon.save()

    dam_row = database.execute_sql("SELECT dam, yeardam FROM Pigeons_orig WHERE dam != '' AND band=? AND year=?",
                                   (pigeon.band_number, pigeon.band_year)).fetchone()
    if dam_row is not None:
        try:
            dam = Pigeon.get((Pigeon.band_number == dam_row["dam"]) &
                             (Pigeon.band_year == dam_row["yeardam"]))
        except Pigeon.DoesNotExist:
            _insert_pigeon(dam_row["dam"], dam_row["yeardam"], enums.Sex.hen, False)
        else:
            pigeon.dam = dam
            pigeon.save()


def _migrate_status(pigeon, old_pindex):
    status_row = database.execute_sql("SELECT active FROM Pigeons_orig WHERE pindex=?;", (old_pindex,)).fetchone()
    if status_row is None:
        return
    status_id = int(status_row["active"])
    status_data = {"pigeon": pigeon, "status_id": status_id}
    if status_id == enums.Status.dead:
        data = database.execute_sql("SELECT * FROM Dead WHERE pindex=?;", (old_pindex,)).fetchone()
        if data is None:
            data = defaultdict(str)
        status_data.update(date=_to_date(data["date"]), info=data["info"])
    elif status_id == enums.Status.sold:
        data = database.execute_sql("SELECT * FROM Sold WHERE pindex=?;", (old_pindex,)).fetchone()
        if data is None:
            data = defaultdict(str)
        status_data.update(person=data["person"], date=_to_date(data["date"]), info=data["info"])
    elif status_id == enums.Status.lost:
        data = database.execute_sql("SELECT * FROM Lost WHERE pindex=?;", (old_pindex,)).fetchone()
        if data is None:
            data = defaultdict(str)
        status_data.update(racepoint=data["racepoint"], date=_to_date(data["date"]), info=data["info"])
    elif status_id == enums.Status.breeder:
        data = database.execute_sql("SELECT * FROM Breeder WHERE pindex=?;", (old_pindex,)).fetchone()
        if data is None:
            data = defaultdict(str)
        status_data.update(start=_to_date(data["start"]), end=_to_date(data["end"]), info=data["info"])
    elif status_id == enums.Status.loaned:
        data = database.execute_sql("SELECT * FROM Onloan WHERE pindex=?;", (old_pindex,)).fetchone()
        if data is None:
            data = defaultdict(str)
        status_data.update(start=_to_date(data["loaned"]), end=_to_date(data["back"]),
                           info=data["info"], person=data["person"])
    elif status_id == enums.Status.widow:
        data = database.execute_sql("SELECT * FROM Widow WHERE pindex=?;", (old_pindex,)).fetchone()
        if data is None:
            data = defaultdict(str)
        status_data.update(partner=_pigeon_for_pindex(data["partner"]), info=data["info"])

    Status.insert(**status_data).execute()


def _migrate_images(pigeon, old_pindex):
    row = database.execute_sql("SELECT image FROM Pigeons_orig WHERE image != '' AND pindex=?;",
                               (old_pindex,)).fetchone()
    if row is not None:
        Image.insert(pigeon=pigeon, path=row["image"], main=True).execute()


def _migrate_results(pigeon, old_pindex):
    cursor = database.execute_sql("SELECT * FROM Results_orig WHERE pindex=?;", (old_pindex,))
    for result in cursor.fetchall():
        result_new = {
            "date": _to_date(result["date"]),
            "racepoint": result["point"],
            "place": int(result["place"]),
            "out": int(result["out"]),
            "category": result["category"],
            "type": result["type"],
            "sector": result["sector"],
            "speed": float(result["speed"]),
            "weather": result["weather"],
            "wind": result["wind"],
            "windspeed": result["windspeed"],
            "comment": result["comment"],
        }
        try:
            Result.insert(pigeon=pigeon, **result_new).execute()
        except IntegrityError:
            # There is a new constraint on multiple columns to avoid duplicate results. This
            # means we'll have to skip those here to avoid conflicts.
            continue


def _migrate_media(pigeon, old_pindex):
    cursor = database.execute_sql("SELECT * FROM Media_orig WHERE pindex=?;", (old_pindex,))
    for media in cursor.fetchall():
        media_new = {
            "path": media["path"],
            "type": media["type"],
            "title": media["title"],
            "description": media["description"],
        }
        Media.insert(pigeon=pigeon, **media_new).execute()


def _migrate_breeding():
    cursor = database.execute_sql("SELECT * FROM Breeding_orig;")
    for row in cursor.fetchall():
        breeding_data = {
            "sire": _pigeon_for_pindex(row["sire"]),
            "dam": _pigeon_for_pindex(row["dam"]),
            "date": _to_date(row["date"]),
            "laid1": _to_date(row["laid1"]),
            "hatched1": _to_date(row["hatched1"]),
            "child1": _pigeon_for_pindex(row["pindex1"]),
            "success1": bool(row["success1"]),
            "laid2": _to_date(row["laid2"]),
            "hatched2": _to_date(row["hatched2"]),
            "child2": _pigeon_for_pindex(row["pindex2"]),
            "success2": bool(row["success2"]),
            "clutch": row["clutch"],
            "box": row["box"],
            "comment": row["comment"],
        }
        # Previous versions weren't so strict about the existence of a sire and dam
        # in the database. The new schema requires them. If none of them exist in the
        # the database, remove the breeding record. If only one of them doesn't exist,
        # add it to the database as a hidden pigeon.
        if breeding_data["sire"] is None and breeding_data["dam"] is None:
            continue
        if breeding_data["sire"] is None:
            band, year = _split_pindex(row["sire"])
            breeding_data["sire"] = _insert_pigeon(band, year, enums.Sex.cock, False)
        if breeding_data["dam"] is None:
            band, year = _split_pindex(row["dam"])
            breeding_data["dam"] = _insert_pigeon(band, year, enums.Sex.hen, False)
        Breeding.insert(**breeding_data).execute()


def _migrate_medication():
    cursor = database.execute_sql("SELECT *, GROUP_CONCAT(pindex, ',') AS pindexes "
                                  "FROM Medication_orig GROUP BY medid;")
    for row in cursor:
        pigeons = [_pigeon_for_pindex(pindex) for pindex in row["pindexes"].split(",")]
        pigeons = [pigeon for pigeon in pigeons if pigeon is not None]
        medication_data = {
            "date": _to_date(row["date"]),
            "description": row["description"],
            "doneby": row["doneby"],
            "medication": row["medication"],
            "dosage": row["dosage"],
            "comment": row["comment"],
            "vaccination": bool(row["vaccination"]),
        }
        # This is slower than doing a model.insert(), but that doesn't seem to work with the M2M field.
        med = Medication.create(**medication_data)
        med.pigeons.add(pigeons)


def _migrate_data_tables():
    cursor = database.execute_sql("SELECT * FROM Addresses_orig;")
    for row in cursor.fetchall():
        person_data = {
            "name": row["name"],
            "me": bool(row["me"]),
            "street": row["street"],
            "zipcode": row["code"],
            "city": row["city"],
            "country": row["country"],
            "phone": row["phone"],
            "email": row["email"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "comment": row["comment"],
        }
        Person.insert(**person_data).execute()

    Category.insert_from(SQL("SELECT category FROM Categories_orig;"), ["category"]).execute()
    Colour.insert_from(SQL("SELECT colour FROM Colours_orig;"), ["colour"]).execute()
    Loft.insert_from(SQL("SELECT loft FROM Lofts_orig;"), ["loft"]).execute()
    Racepoint.insert_from(
        SQL("SELECT racepoint, distance, unit, xco, yco FROM Racepoints_orig;"),
        ["racepoint", "distance", "unit", "xco", "yco"]).execute()
    Sector.insert_from(SQL("SELECT sector FROM Sectors_orig;"), ["sector"]).execute()
    Strain.insert_from(SQL("SELECT strain FROM Strains_orig;"), ["strain"]).execute()
    Type.insert_from(SQL("SELECT type FROM Types_orig;"), ["type"]).execute()
    Weather.insert_from(SQL("SELECT weather FROM Weather_orig;"), ["weather"]).execute()
    Wind.insert_from(SQL("SELECT wind FROM Wind_orig;"), ["wind"]).execute()


#################################
# Initial Peewee database schema.

database = SqliteDatabase(None)


def all_tables():
    tables = []
    for name, obj in globals().items():
        try:
            if issubclass(obj, BaseModel) and obj != BaseModel:
                tables.append(obj)
        except TypeError:
            continue
    tables.append(PigeonMedication)
    return tables


class BaseModel(Model):
    class Meta:
        database = database


class UpgradeDummy(BaseModel):
    dummy = TextField(null=True)

    class Meta:
        table_name = "upgrade_dummy"


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


class Image(BaseModel):
    pigeon = ForeignKeyField(Pigeon, backref="images", on_delete="CASCADE")
    path = CharField()
    main = BooleanField()

    class Meta:
        table_name = "image"


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


class Media(BaseModel):
    pigeon = ForeignKeyField(Pigeon, backref="media", on_delete="CASCADE")
    path = CharField()
    type = CharField()
    title = CharField(default="")
    description = TextField(default="")

    class Meta:
        table_name = "media"


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


class Person(BaseModel):
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


class Category(BaseModel):
    category = CharField(unique=True, constraints=[Check("category != ''")])

    class Meta:
        table_name = "category"


class Colour(BaseModel):
    colour = CharField(unique=True, constraints=[Check("colour != ''")])

    class Meta:
        table_name = "colour"


class Loft(BaseModel):
    loft = CharField(unique=True, constraints=[Check("loft != ''")])

    class Meta:
        table_name = "loft"


class Racepoint(BaseModel):
    racepoint = CharField(unique=True, constraints=[Check("racepoint != ''")])
    distance = CharField(default="")
    unit = IntegerField(default=0)
    xco = CharField(default="")
    yco = CharField(default="")

    class Meta:
        table_name = "racepoint"


class Sector(BaseModel):
    sector = CharField(unique=True, constraints=[Check("sector != ''")])

    class Meta:
        table_name = "sector"


class Strain(BaseModel):
    strain = CharField(unique=True, constraints=[Check("strain != ''")])

    class Meta:
        table_name = "strain"


class Type(BaseModel):
    type = CharField(unique=True, constraints=[Check("type != ''")])

    class Meta:
        table_name = "type"


class Weather(BaseModel):
    weather = CharField(unique=True, constraints=[Check("weather != ''")])

    class Meta:
        table_name = "weather"


class Wind(BaseModel):
    wind = CharField(unique=True, constraints=[Check("wind != ''")])

    class Meta:
        table_name = "wind"
