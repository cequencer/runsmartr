#!/usr/bin/env python


import pandas as pd
from shapely.geometry import Point, MultiPoint
from sqlalchemy import *
from geoalchemy2 import Geometry


def main():

    # Read from file and get rid of duplicates
    datafile = 'mmf/routes_all_SF.dat'
    routes_SF = pd.io.parsers.read_table(datafile, sep=' ',
                                         header=None, names=['ID','lng','lat'],
                                         index_col=None)
    routes_SF.drop_duplicates(inplace=True)
    routes_SF.sort(inplace=True)

    print 'Imported'

    # Convert lnt,lat to shapely Points and make pandas dataframe
    mmf_routes = pd.DataFrame({
        'point': [ Point(lng,lat).wkt for lng, lat
                  in routes_SF[['lng', 'lat']].values.tolist() ],
        'mmf_id': routes_SF['ID'].values.tolist()})
                         
    print 'Converted to shapes'

    # Add table to database 'runhere'
    engine = create_engine('postgresql://andy:po9uwe5@localhost:5432/runhere')
    metadata = MetaData(engine)
    my_table = Table('mmf_routes', metadata,
        Column('mmf_id', Integer, primary_key=True),
        Column('point', Geometry('POINT')))
    my_table.create(engine)
    conn = engine.connect()
    ins = my_table.insert()
    conn.execute(my_table.insert(), mmf_routes.to_dict('records'))

    print 'Wrote to DB'

    return


if __name__ == '__main__':
    main()
