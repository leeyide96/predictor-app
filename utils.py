from sklearn.base import (BaseEstimator,
                          TransformerMixin)
from geopy.distance import geodesic

class MeanEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, column):
        self.column = column
        self.encoding = None
        self.inverse_encoding = None

    def fit(self, X):
        counts = X.groupby(self.column).resale_price.mean().sort_values()
        self.encoding = {cat: i for i, cat in enumerate(counts.index)}
        self.inverse_encoding = {i: cat for cat, i in self.encoding.items()}
        return self

    def transform(self, X):
        return X[self.column].apply(lambda x: self.encoding[x])

    def inverse_transform(self, X):
        return X.apply(lambda x: self.inverse_encoding[x])
    
def count_nearby(x, df, radius_km, name_col, latlong_col='latlong'):
    """
    Add a column to houses_df counting number of facilities within specified radius.

    Parameters:
    df: DataFrame containing another data with latlong column
    radius_km: Radius in kilometers to search for nearby facilities
    name_col: Name of column you want to get the names from the nearby facilities
    latlong_col: Name of the column containing (lat, long) tuples

    """
    x_loc = eval(x) if isinstance(x, str) else x
    df[latlong_col] = df[latlong_col].apply(lambda x: eval(x) if isinstance(x, str) else x)

    df["km"] = df[latlong_col].apply(lambda x: geodesic(x_loc, x))
    count = df[df["km"] <= radius_km].shape[0]
    nearest = round(df["km"].min().km, 1)
    facilities = df[df["km"] <= radius_km].sort_values("km")[name_col].unique().tolist()

    return count, nearest, facilities


