import pgdb, re

user   = "gis"
passw  = "gis"
dbname = "gis"
file   = "out.txt"

numre  = re.compile("[^0-9]")

bothquery  = """UPDATE planet_osm_point SET population= %s, "name:en" = %s WHERE osm_id = %s"""
popquery   = """UPDATE planet_osm_point SET population = %s WHERE osm_id = %s"""
namequery  = """UPDATE planet_osm_point SET "name:en" = %s WHERE osm_id = %s"""

def do_insert(cur, osmid, name_en = None, population = None):
    if name_en is not None and population is not None:
        cur.execute(bothquery, (population, name_en, osmid))
    elif name_en is not None:
        cur.execute(namequery, (name_en, osmid))
    elif population is not None:
        cur.execute(popquery, (population, osmid))

try:
    db = pgdb.connect(database=dbname, user=user, password=passw)
    cur = db.cursor()
    f = open(file)
    count = 0
    for line in f:
        data = eval(line)
        osmid = data.get('id')
        name  = data.get('name:en')
        pop   = data.get('population')
        if pop is not None:
            # clean out any crazy non-numerics used to punctuate the number
            pop = numre.sub('', pop)
            if pop == '':
                pop = None
        do_insert(cur, osmid, name, pop)
        count = count + 1
        if count % 100 == 0:
            print count
    db.commit()
    cur.close()
    db.close()

except Exception, e:
    raise
#     print "failed with exception: %e" % e
#     db.rollback()
#     cur.close()
#     db.close()
