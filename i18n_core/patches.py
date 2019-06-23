from platform_utils import paths
import pickle
import babel.core

if paths.is_frozen():
    import pytz

    pytz.resource_exists = lambda name: False
    with open(
        os.path.join(paths.embedded_data_path(), "babel", "global.dat"), "rb"
    ) as fp:
        babel.core._global_data = pickle.load(fp)

import babel.localedata

if paths.is_frozen():
    babel.localedata._dirname = os.path.join(paths.embedded_data_path(), "locale-data")

