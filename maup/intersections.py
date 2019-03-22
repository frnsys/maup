from geopandas import GeoDataFrame
import numpy

from .indexed_geometries import IndexedGeometries
from .indices import get_geometries_with_range_index


def intersections(sources, targets):
    """Computes all of the nonempty intersections between two sets of geometries.
    The returned `~geopandas.GeoSeries` will have a MultiIndex, where the geometry
    at index *(i, j)* is the intersection of ``sources[i]`` and ``targets[j]``
    (if it is not empty).

    :param sources: geometries
    :type sources: :class:`~geopandas.GeoSeries` or :class:`~geopandas.GeoDataFrame`
    :param targets: geometries
    :type targets: :class:`~geopandas.GeoSeries` or :class:`~geopandas.GeoDataFrame`
    :rtype: :class:`~geopandas.GeoSeries`
    """
    reindexed_sources = get_geometries_with_range_index(sources)
    reindexed_targets = get_geometries_with_range_index(targets)
    spatially_indexed_sources = IndexedGeometries(reindexed_sources)

    records = [
        # Flip i, j to j, i so that the index is ["source", "target"]
        (sources.index[j], targets.index[i], geometry)
        for i, j, geometry in spatially_indexed_sources.enumerate_intersections(
            reindexed_targets
        )
    ]
    df = GeoDataFrame.from_records(records, columns=["source", "target", "geometry"])
    geometries = df.set_index(["source", "target"]).geometry
    geometries.sort_index(inplace=True)
    return geometries


def interpolate(inters, data, weights, aggregate_by=numpy.sum):
    """
    :param inters: the :func:`~maup.intersections` of the geometries you are
        interpolating from (sources) and the geometries you are interpolating to
    :param data: the data you want to interpolate (must be indexed the same as
        the source geometries)
    :param weights: the weights to use when prorating from ``sources`` to
        ``inters``
    :param aggregate_by: (optional) the function to use for aggregating from
        ``inters`` to ``targets``. The default is :func:`numpy.sum`.
    """
    prorated = inters.index.get_level_values("source").map(data) * weights
    interpolated = prorated.groupby(level="target").agg(aggregate_by)
    return interpolated
