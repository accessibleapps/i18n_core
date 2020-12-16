from platform_utils import paths
import os
import pickle

if paths.is_frozen():
    import babel.core

    with open(
        os.path.join(paths.embedded_data_path(), "babel", "global.dat"), "rb"
    ) as fp:
        babel.core._global_data = pickle.load(fp)

    import babel.localedata

    babel.localedata._dirname = os.path.join(paths.embedded_data_path(), "locale-data")

