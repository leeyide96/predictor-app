from sklearn.base import (BaseEstimator,
                          TransformerMixin)
from geopy.distance import geodesic

class MeanEncoder(BaseEstimator, TransformerMixin):
    """
    A custom transformer for encoding categorical variables based on their mean value.

    Parameter:
        column (str): Name of the categorical column to encode
    """
    def __init__(self, column):
        self.column = column
        self.encoding = None
        self.inverse_encoding = None

    def fit(self, X):
        """
        Fits the encoder by computing mean resale prices for each category.

        Parameters:
            X (pd.DataFrame): Input DataFrame containing the categorical column and resale_price

        Returns:
            self: The fitted encoder instance
        """
        counts = X.groupby(self.column).resale_price.mean().sort_values()
        self.encoding = {cat: i for i, cat in enumerate(counts.index)}
        self.inverse_encoding = {i: cat for cat, i in self.encoding.items()}
        return self

    def transform(self, X):
        """
        Transforms categorical values to their encoded values.

        Parameters:
            X (pd.DataFrame): Input DataFrame containing the categorical column

        Returns:
            pd.Series: Encoded values
        """
        return X[self.column].apply(lambda x: self.encoding[x])

    def inverse_transform(self, X):
        """
        Converts encoded values back to original categories.

        Parameters:
            X (pd.Series): Series of encoded values

        Returns:
            pd.Series: Original categorical values
        """
        return X.apply(lambda x: self.inverse_encoding[x])
    
def count_nearby(x, df, radius_km, name_col, latlong_col='latlong'):
    """
    Counts facilities within specified radius of a location and finds nearest distance.

    Parameters:
        x (tuple or str): Reference location coordinates as (lat, long)
        df (pd.DataFrame): DataFrame containing facility locations
        radius_km (float): Search radius in kilometers
        latlong_col (str): Name of column containing (lat, long) tuples

    Returns:
        tuple: (count of nearby facilities, distance to nearest facility in km, names of facilities within radius)
    """
    x_loc = eval(x) if isinstance(x, str) else x
    df[latlong_col] = df[latlong_col].apply(lambda x: eval(x) if isinstance(x, str) else x)

    df["km"] = df[latlong_col].apply(lambda x: geodesic(x_loc, x))
    count = df[df["km"] <= radius_km].shape[0]
    nearest = round(df["km"].min().km, 1)
    facilities = df[df["km"] <= radius_km].sort_values("km")[name_col].unique().tolist()

    return count, nearest, facilities


